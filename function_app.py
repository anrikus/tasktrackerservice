"""
Azure Functions app for TaskTracker ML probe predictions.

This module provides HTTP endpoints for:
- Health checking
- Listing available trained probes
- Making predictions using linear probes on model activations
"""

import json
import logging
import pickle
from pathlib import Path
from typing import List

import azure.functions as func
import numpy as np
from pydantic import BaseModel, Field, ValidationError, field_validator

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Pydantic Models for Request/Response Validation
class PredictRequest(BaseModel):
    """Request model for prediction endpoint with activation validation."""

    model: str = Field(..., description="Model name (e.g., 'llama3_8b')")
    probe_type: str = Field(default="linear_probe",
                            description="Type of probe")
    layer: int = Field(..., ge=0, description="Layer number (must be >= 0)")
    primary_activations: List[float] = Field(
        ..., description="Primary activation values"
    )
    text_activations: List[float] = Field(...,
                                          description="Text activation values")

    @field_validator("primary_activations", "text_activations")
    @classmethod
    def validate_activations_length(cls, v: List[float]) -> List[float]:
        """Validate that activation arrays have exactly 4096 dimensions."""
        if len(v) != 4096:
            raise ValueError("Activations must have exactly 4096 dimensions")
        return v


class PredictResponse(BaseModel):
    """Response model for prediction endpoint results."""

    model: str
    probe_type: str
    layer: int
    predicted_probability: float = Field(..., ge=0.0, le=1.0)


class ProbeInfo(BaseModel):
    """Information about an available probe including supported layers."""

    model: str
    probe_type: str
    layers: List[int]


class ProbesResponse(BaseModel):
    """Response model containing list of available probes."""

    probes: List[ProbeInfo]


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


def _get_available_layers(model_dir: Path) -> List[int]:
    """Get list of available layers for a model directory."""
    layers = []
    for layer_dir in sorted(model_dir.iterdir()):
        if layer_dir.is_dir() and layer_dir.name.isdigit():
            layer_num = int(layer_dir.name)
            config_file = layer_dir / "config.json"
            model_file = layer_dir / "model.pickle"

            if config_file.exists() and model_file.exists():
                layers.append(layer_num)
    return layers


def _discover_probes(probes_dir: Path) -> List[ProbeInfo]:
    """Discover all available probes in the probes directory."""
    probes: List[ProbeInfo] = []
    if not probes_dir.exists():
        return probes

    for model_dir in probes_dir.iterdir():
        if not model_dir.is_dir():
            continue

        layers = _get_available_layers(model_dir)
        if layers:
            probe_info = ProbeInfo(
                model=model_dir.name, probe_type="linear_probe", layers=layers
            )
            probes.append(probe_info)
    return probes


@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse: 
    """Health check endpoint"""
    logging.info("Health check endpoint was triggered.")

    return func.HttpResponse(
        json.dumps(
            {"status": "healthy", "message": "TaskTracker API is running"}),
        status_code=200,
        mimetype="application/json",
    )


@app.route(route="v1/predict", methods=["POST"])
def predict(req: func.HttpRequest) -> func.HttpResponse:
    """Main prediction endpoint"""
    logging.info("Predict endpoint was triggered.")

    try:
        # Parse and validate request using Pydantic
        request_data = PredictRequest.model_validate_json(req.get_body())
        logging.info(
            "Request validated for model: %s, layer: %s",
            request_data.model,
            request_data.layer,
        )

        # Load the probe
        probe_dir = (
            Path(__file__).parent
            / "models"
            / "trained_linear_probes"
            / request_data.model
            / str(request_data.layer)
        )
        model_file = probe_dir / "model.pickle"

        if not model_file.exists():
            error_msg = (
                f"Probe not found for model '{request_data.model}' "
                f"at layer {request_data.layer}"
            )
            return func.HttpResponse(
                json.dumps({"error": error_msg}),
                status_code=404,
                mimetype="application/json",
            )

        # Load the probe model
        with open(model_file, "rb") as f:
            probe_model = pickle.load(f)

        logging.info(
            # Compute delta and make prediction
            "Successfully loaded probe for %s layer %s",
            request_data.model,
            request_data.layer,
        )
        primary_activations = np.array(request_data.primary_activations)
        text_activations = np.array(request_data.text_activations)
        delta = primary_activations - text_activations

        # Reshape for model input
        if len(delta.shape) == 1:
            delta = delta.reshape(1, -1)

        # Get prediction probability
        if hasattr(probe_model, "predict_proba"):
            prediction_proba = probe_model.predict_proba(delta)
            predicted_probability = (
                float(prediction_proba[0][1])
                if prediction_proba.shape[1] > 1
                else float(prediction_proba[0][0])
            )
        elif hasattr(probe_model, "predict"):
            prediction = probe_model.predict(delta)
            predicted_probability = float(prediction[0])
        else:
            return func.HttpResponse(
                json.dumps(
                    {"error": "Probe model does not support prediction"}),
                status_code=500,
                mimetype="application/json",
            )

        # Create and return response using Pydantic
        logging.info("Predicted probability: %s", predicted_probability)
        response = PredictResponse(
            model=request_data.model,
            probe_type=request_data.probe_type,
            layer=request_data.layer,
            predicted_probability=predicted_probability,
        )

        return func.HttpResponse(
            response.model_dump_json(), status_code=200, mimetype="application/json"
        )

    except ValidationError as e:
        logging.error("Validation error: %s", e)
        return func.HttpResponse(
            json.dumps(
                {
                    "error": "Validation failed",
                    "details": [
                        {"field": err["loc"][-1], "message": err["msg"]}
                        for err in e.errors()
                    ],
                }
            ),
            status_code=400,
            mimetype="application/json",
        )
    except FileNotFoundError as e:
        logging.error("Probe file not found: %s", e)
        return func.HttpResponse(
            json.dumps({"error": "Probe file not found"}),
            status_code=404,
            mimetype="application/json",
        )
    except Exception as e:  # pylint: disable=broad-except
        # Catch all unexpected errors to ensure HTTP endpoint always returns a response
        logging.error("Error in predict endpoint: %s", str(e))
        return func.HttpResponse(
            json.dumps({"error": "Internal server error: " + str(e)}),
            status_code=500,
            mimetype="application/json",
        )


@app.route(route="v1/probes", methods=["GET"])
def list_probes(req: func.HttpRequest) -> func.HttpResponse:
    """List available probes endpoint"""
    logging.info("List probes endpoint was triggered.")

    try:
        # Path to the trained linear probes directory
        probes_dir = Path(__file__).parent / \
            "models" / "trained_linear_probes"

        # Discover all available probes
        probes = _discover_probes(probes_dir)

        response = ProbesResponse(probes=probes)
        return func.HttpResponse(
            response.model_dump_json(), status_code=200, mimetype="application/json"
        )

    except Exception as e:  # pylint: disable=broad-except
        # Catch all unexpected errors to ensure HTTP endpoint always returns a response
        logging.error("Error in list_probes endpoint: %s", str(e))
        return func.HttpResponse(
            json.dumps({"error": "Internal server error: " + str(e)}),
            status_code=500,
            mimetype="application/json",
        )
