from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Path as PathParam,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
)

from config import settings


router = APIRouter(
    tags=["Test"],
    prefix=settings.url.test,
)


APP_DIR = Path(__file__).resolve().parents[1]

UPLOAD_DIR = APP_DIR / "static" / "uploads"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


@router.get("")
def index():
    return {
        "message": "Hello, World!"
    }


# --------------------------------------------------
# 1. BODY
# --------------------------------------------------


class TestBodyItem(BaseModel):
    name: str

    description: str | None = None

    price: float = Field(
        gt=0,
    )

    tax: float | None = Field(
        default=None,
        ge=0,
    )


@router.post("/body")
async def test_body_example(
    item: TestBodyItem,
):
    return item


# --------------------------------------------------
# 2. QUERY PARAMETERS AND STRING VALIDATIONS
# --------------------------------------------------


@router.get("/query-validation")
async def test_query_validation(
    q: Annotated[
        str | None,
        Query(
            min_length=3,
            max_length=50,
            pattern=r"^[a-zA-Z0-9_-]+$",
        ),
    ] = None,
):
    return {
        "q": q
    }


# --------------------------------------------------
# 3. PATH PARAMETERS AND NUMERIC VALIDATIONS
# --------------------------------------------------


@router.get(
    "/path-validation/{item_id}"
)
async def test_path_numeric_validation(
    item_id: Annotated[
        int,
        PathParam(
            ge=1,
            le=1000,
        ),
    ],
    size: Annotated[
        float,
        Query(
            gt=0,
            le=100,
        ),
    ] = 1.0,
):
    return {
        "item_id": item_id,
        "size": size,
    }


# --------------------------------------------------
# 4. QUERY PARAMETER MODELS
# --------------------------------------------------


class TestFilterParams(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    limit: int = Field(
        default=100,
        gt=0,
        le=100,
    )

    offset: int = Field(
        default=0,
        ge=0,
    )

    order_by: Literal[
        "created_at",
        "updated_at",
    ] = "created_at"

    tags: list[str] = Field(
        default_factory=list,
    )


@router.get("/query-model")
async def test_query_parameter_model(
    filters: Annotated[
        TestFilterParams,
        Query(),
    ],
):
    return filters


# --------------------------------------------------
# 5. NESTED MODELS
# --------------------------------------------------


class TestImage(BaseModel):
    url: HttpUrl
    name: str


class TestNestedItem(BaseModel):
    name: str

    description: str | None = None

    price: float = Field(
        gt=0
    )

    images: list[TestImage] = Field(
        default_factory=list
    )


@router.post("/nested-model")
async def test_nested_model(
    item: TestNestedItem,
):
    return item


# --------------------------------------------------
# 6. REQUEST FORMS
# --------------------------------------------------


@router.post("/form")
async def test_request_form(
    username: Annotated[
        str,
        Form(),
    ],
    password: Annotated[
        str,
        Form(),
    ],
):
    return {
        "username": username
    }


# --------------------------------------------------
# 7. REQUEST FORM MODELS
# --------------------------------------------------


class TestLoginForm(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    username: str = Field(
        min_length=1
    )

    password: str = Field(
        min_length=4
    )


@router.post("/form-model")
async def test_request_form_model(
    data: Annotated[
        TestLoginForm,
        Form(),
    ],
):
    return {
        "username": data.username
    }


# --------------------------------------------------
# 8. FORMAT JSON / HTML
# --------------------------------------------------


@router.get(
    "/format",
    response_model=None,
)
async def test_format_response(
    response_format: Annotated[
        Literal["json", "html"],
        Query(alias="format"),
    ] = "json",
):
    if response_format == "html":
        return HTMLResponse(
            content="""
            <html>
                <body>
                    <h1>
                        FastAPI HTML response
                    </h1>
                    <p>
                        format=html
                    </p>
                </body>
            </html>
            """
        )

    return JSONResponse(
        content={
            "message": "FastAPI JSON response",
            "format": "json",
        }
    )


# --------------------------------------------------
# 9. IMAGE UPLOAD
# --------------------------------------------------


ALLOWED_IMAGE_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}


@router.post(
    "/upload-image",
    status_code=status.HTTP_201_CREATED,
)
async def test_upload_image(
    request: Request,
    file: Annotated[
        UploadFile,
        File(),
    ],
):
    extension = ALLOWED_IMAGE_TYPES.get(
        file.content_type or ""
    )

    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only PNG, JPG and WEBP "
                "images are supported"
            ),
        )

    filename = (
        f"{uuid4().hex}{extension}"
    )

    destination = (
        UPLOAD_DIR / filename
    )

    with destination.open(
        "wb"
    ) as output_file:

        while chunk := await file.read(
            1024 * 1024
        ):
            output_file.write(chunk)

    await file.close()

    file_url = request.url_for(
        "static",
        path=f"uploads/{filename}",
    )

    return {
        "filename": filename,
        "url": str(file_url),
    }