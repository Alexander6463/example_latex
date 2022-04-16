import uuid
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.config import Settings

settings = Settings()


def extract_boxes_from_result(
    classes: Tuple[str],
    result: List[Any],
    size: Dict[str, float],
    page_number: Optional[int] = 1,
    score_thr: float = settings.default_thresholds,
    document: bool = False,
) -> Dict[str, Any]:
    if len(result) == 2:
        bboxes_res, _ = result
    else:
        bboxes_res = result
    bboxes = np.vstack(bboxes_res)  # type: ignore
    labels = [
        np.full(bbox.shape[0], i, dtype=np.int32)
        for i, bbox in enumerate(bboxes_res)
    ]
    labels = np.concatenate(labels)  # type: ignore
    scores = bboxes[:, -1]
    filter_scores_with_threshold = scores > score_thr
    bboxes = bboxes[filter_scores_with_threshold, :]
    labels = labels[filter_scores_with_threshold]
    output: Dict[str, Any] = {
        "page_num": page_number,
        "size": size,
        "objs": [],
    }
    for bbox, label in zip(bboxes, labels):
        if document:
            bbox = [
                i * settings.inch_to_point / settings.dpi
                for i in bbox.astype(np.int32)[:4]
            ]
        else:
            bbox = [float(i) for i in bbox.astype(np.int32)[:4]]
        id = str(uuid.uuid4())
        category = classes[int(label)]
        geom = {"id": id, "bbox": bbox, "category": category}
        output["objs"].append(geom)
    return output


def prepare_response(
    input_result: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    response = {}  # type: ignore
    for page in input_result:
        page_num = page["page_num"]
        for geom in page["objs"]:
            category = geom.get("category", None)
            if not category:
                continue
            id = geom["id"]
            pages_for_label = response.setdefault(category, {})
            ids = pages_for_label.setdefault(page_num, [])
            ids.append(id)
    return response
