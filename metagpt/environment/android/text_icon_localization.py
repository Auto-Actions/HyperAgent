import math
import clip
import cv2
import numpy as np
import torch

import groundingdino.datasets.transforms as T
from groundingdino.models import build_model
from groundingdino.util.slconfig import SLConfig
from groundingdino.util.utils import clean_state_dict, get_phrases_from_posmap
from PIL import Image, ImageDraw


################################## text_localization using ocr #######################
def crop_image(img, position):
    def distance(x1, y1, x2, y2):
        return math.sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2))

    position = position.tolist()
    for i in range(4):
        for j in range(i + 1, 4):
            if position[i][0] > position[j][0]:
                tmp = position[j]
                position[j] = position[i]
                position[i] = tmp
    if position[0][1] > position[1][1]:
        tmp = position[0]
        position[0] = position[1]
        position[1] = tmp

    if position[2][1] > position[3][1]:
        tmp = position[2]
        position[2] = position[3]
        position[3] = tmp

    x1, y1 = position[0][0], position[0][1]
    x2, y2 = position[2][0], position[2][1]
    x3, y3 = position[3][0], position[3][1]
    x4, y4 = position[1][0], position[1][1]

    corners = np.zeros((4, 2), np.float32)
    corners[0] = [x1, y1]
    corners[1] = [x2, y2]
    corners[2] = [x4, y4]
    corners[3] = [x3, y3]

    img_width = distance((x1 + x4) / 2, (y1 + y4) / 2, (x2 + x3) / 2, (y2 + y3) / 2)
    img_height = distance((x1 + x2) / 2, (y1 + y2) / 2, (x4 + x3) / 2, (y4 + y3) / 2)

    corners_trans = np.zeros((4, 2), np.float32)
    corners_trans[0] = [0, 0]
    corners_trans[1] = [img_width - 1, 0]
    corners_trans[2] = [0, img_height - 1]
    corners_trans[3] = [img_width - 1, img_height - 1]

    transform = cv2.getPerspectiveTransform(corners, corners_trans)
    dst = cv2.warpPerspective(img, transform, (int(img_width), int(img_height)))
    return dst


def calculate_size(box):
    return (box[2] - box[0]) * (box[3] - box[1])


def order_point(coor):
    arr = np.array(coor).reshape([4, 2])
    sum_ = np.sum(arr, 0)
    centroid = sum_ / arr.shape[0]
    theta = np.arctan2(arr[:, 1] - centroid[1], arr[:, 0] - centroid[0])
    sort_points = arr[np.argsort(theta)]
    sort_points = sort_points.reshape([4, -1])
    if sort_points[0][0] > centroid[0]:
        sort_points = np.concatenate([sort_points[3:], sort_points[:3]])
    sort_points = sort_points.reshape([4, 2]).astype("float32")
    return sort_points


def longest_common_substring_length(str1, str2):
    m = len(str1)
    n = len(str2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[m][n]


def ocr(image_path, prompt, ocr_detection, ocr_recognition, x, y):
    text_data = []
    coordinate = []
    image = Image.open(image_path)
    iw, ih = image.size

    image_full = cv2.imread(image_path)
    det_result = ocr_detection(image_full)
    det_result = det_result["polygons"]
    for i in range(det_result.shape[0]):
        pts = order_point(det_result[i])
        image_crop = crop_image(image_full, pts)
        result = ocr_recognition(image_crop)["text"][0]

        if result == prompt:
            box = [int(e) for e in list(pts.reshape(-1))]
            box = [box[0], box[1], box[4], box[5]]

            if calculate_size(box) > 0.05 * iw * ih:
                continue

            text_data.append(
                [
                    int(max(0, box[0] - 10) * x / iw),
                    int(max(0, box[1] - 10) * y / ih),
                    int(min(box[2] + 10, iw) * x / iw),
                    int(min(box[3] + 10, ih) * y / ih),
                ]
            )
            coordinate.append(
                [
                    int(max(0, box[0] - 300) * x / iw),
                    int(max(0, box[1] - 400) * y / ih),
                    int(min(box[2] + 300, iw) * x / iw),
                    int(min(box[3] + 400, ih) * y / ih),
                ]
            )

    max_length = 0
    if len(text_data) == 0:
        for i in range(det_result.shape[0]):
            pts = order_point(det_result[i])
            image_crop = crop_image(image_full, pts)
            result = ocr_recognition(image_crop)["text"][0]

            if len(result) < 0.3 * len(prompt):
                continue

            if result in prompt:
                now_length = len(result)
            else:
                now_length = longest_common_substring_length(result, prompt)

            if now_length > max_length:
                max_length = now_length
                box = [int(e) for e in list(pts.reshape(-1))]
                box = [box[0], box[1], box[4], box[5]]

                text_data = [
                    [
                        int(max(0, box[0] - 10) * x / iw),
                        int(max(0, box[1] - 10) * y / ih),
                        int(min(box[2] + 10, iw) * x / iw),
                        int(min(box[3] + 10, ih) * y / ih),
                    ]
                ]
                coordinate = [
                    [
                        int(max(0, box[0] - 300) * x / iw),
                        int(max(0, box[1] - 400) * y / ih),
                        int(min(box[2] + 300, iw) * x / iw),
                        int(min(box[3] + 400, ih) * y / ih),
                    ]
                ]

        if len(prompt) <= 10:
            if max_length >= 0.8 * len(prompt):
                return text_data, coordinate
            else:
                return [], []
        elif (len(prompt) > 10) and (len(prompt) <= 20):
            if max_length >= 0.5 * len(prompt):
                return text_data, coordinate
            else:
                return [], []
        else:
            if max_length >= 0.4 * len(prompt):
                return text_data, coordinate
            else:
                return [], []

    else:
        return text_data, coordinate


################################## icon_localization using clip #######################


def calculate_iou(box1, box2):
    xA = max(box1[0], box2[0])
    yA = max(box1[1], box2[1])
    xB = min(box1[2], box2[2])
    yB = min(box1[3], box2[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    box1Area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2Area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    unionArea = box1Area + box2Area - interArea
    iou = interArea / unionArea

    return iou


def crop(image, box, i, text_data=None):
    image = Image.open(image)

    if text_data:
        draw = ImageDraw.Draw(image)
        draw.rectangle(((text_data[0], text_data[1]), (text_data[2], text_data[3])), outline="red", width=5)
        # font_size = int((text_data[3] - text_data[1])*0.75)
        # font = ImageFont.truetype("arial.ttf", font_size)
        # draw.text((text_data[0]+5, text_data[1]+5), str(i), font=font, fill="red")

    cropped_image = image.crop(box)
    cropped_image.save(f"./temp/{i}.jpg")


def in_box(box, target):
    if (box[0] > target[0]) and (box[1] > target[1]) and (box[2] < target[2]) and (box[3] < target[3]):
        return True
    else:
        return False


def crop_for_clip(image, box, i, position):
    image = Image.open(image)
    w, h = image.size
    if position == "left":
        bound = [0, 0, w / 2, h]
    elif position == "right":
        bound = [w / 2, 0, w, h]
    elif position == "top":
        bound = [0, 0, w, h / 2]
    elif position == "bottom":
        bound = [0, h / 2, w, h]
    elif position == "top left":
        bound = [0, 0, w / 2, h / 2]
    elif position == "top right":
        bound = [w / 2, 0, w, h / 2]
    elif position == "bottom left":
        bound = [0, h / 2, w / 2, h]
    elif position == "bottom right":
        bound = [w / 2, h / 2, w, h]
    else:
        bound = [0, 0, w, h]

    if in_box(box, bound):
        cropped_image = image.crop(box)
        cropped_image.save(f"./temp/{i}.jpg")
        return True
    else:
        return False


def clip_for_icon(clip_model, clip_preprocess, images, prompt):
    image_features = []
    for image_file in images:
        image = clip_preprocess(Image.open(image_file)).unsqueeze(0).to(next(clip_model.parameters()).device)
        image_feature = clip_model.encode_image(image)
        image_features.append(image_feature)
    image_features = torch.cat(image_features)

    text = clip.tokenize([prompt]).to(next(clip_model.parameters()).device)
    text_features = clip_model.encode_text(text)

    image_features /= image_features.norm(dim=-1, keepdim=True)
    text_features /= text_features.norm(dim=-1, keepdim=True)
    similarity = (100.0 * image_features @ text_features.T).softmax(dim=0).squeeze(0)
    _, max_pos = torch.max(similarity, dim=0)
    pos = max_pos.item()

    return pos


def transform_image(image_pil):
    transform = T.Compose(
        [
            T.RandomResize([800], max_size=1333),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    image, _ = transform(image_pil, None)  # 3, h, w
    return image


def load_model(model_config_path, model_checkpoint_path, device):
    args = SLConfig.fromfile(model_config_path)
    args.device = device
    model = build_model(args)
    checkpoint = torch.load(model_checkpoint_path, map_location="cpu")
    load_res = model.load_state_dict(clean_state_dict(checkpoint["model"]), strict=False)
    print(load_res)
    _ = model.eval()
    return model


def get_grounding_output(model, image, caption, box_threshold, text_threshold, with_logits=True):
    caption = caption.lower()
    caption = caption.strip()
    if not caption.endswith("."):
        caption = caption + "."

    with torch.no_grad():
        outputs = model(image[None], captions=[caption])
    logits = outputs["pred_logits"].cpu().sigmoid()[0]  # (nq, 256)
    boxes = outputs["pred_boxes"].cpu()[0]  # (nq, 4)
    logits.shape[0]

    logits_filt = logits.clone()
    boxes_filt = boxes.clone()
    filt_mask = logits_filt.max(dim=1)[0] > box_threshold
    logits_filt = logits_filt[filt_mask]  # num_filt, 256
    boxes_filt = boxes_filt[filt_mask]  # num_filt, 4
    logits_filt.shape[0]

    tokenlizer = model.tokenizer
    tokenized = tokenlizer(caption)

    pred_phrases = []
    scores = []
    for logit, box in zip(logits_filt, boxes_filt):
        pred_phrase = get_phrases_from_posmap(logit > text_threshold, tokenized, tokenlizer)
        if with_logits:
            pred_phrases.append(pred_phrase + f"({str(logit.max().item())[:4]})")
        else:
            pred_phrases.append(pred_phrase)
        scores.append(logit.max().item())

    return boxes_filt, torch.Tensor(scores), pred_phrases


def remove_boxes(boxes_filt, size, iou_threshold=0.5):
    boxes_to_remove = set()

    for i in range(len(boxes_filt)):
        if calculate_size(boxes_filt[i]) > 0.05 * size[0] * size[1]:
            boxes_to_remove.add(i)
        for j in range(len(boxes_filt)):
            if calculate_size(boxes_filt[j]) > 0.05 * size[0] * size[1]:
                boxes_to_remove.add(j)
            if i == j:
                continue
            if i in boxes_to_remove or j in boxes_to_remove:
                continue
            iou = calculate_iou(boxes_filt[i], boxes_filt[j])
            if iou >= iou_threshold:
                boxes_to_remove.add(j)

    boxes_filt = [box for idx, box in enumerate(boxes_filt) if idx not in boxes_to_remove]

    return boxes_filt


def det(input_image, text_prompt, groundingdino_model, box_threshold=0.05, text_threshold=0.5):
    image = Image.open(input_image)
    size = image.size

    image_pil = image.convert("RGB")
    image = np.array(image_pil)

    transformed_image = transform_image(image_pil)
    boxes_filt, scores, pred_phrases = get_grounding_output(
        groundingdino_model, transformed_image, text_prompt, box_threshold, text_threshold
    )

    H, W = size[1], size[0]
    for i in range(boxes_filt.size(0)):
        boxes_filt[i] = boxes_filt[i] * torch.Tensor([W, H, W, H])
        boxes_filt[i][:2] -= boxes_filt[i][2:] / 2
        boxes_filt[i][2:] += boxes_filt[i][:2]

    boxes_filt = boxes_filt.cpu().int().tolist()
    filtered_boxes = remove_boxes(boxes_filt, size)  # [:9]
    coordinate = []
    image_data = []
    for box in filtered_boxes:
        image_data.append(
            [max(0, box[0] - 10), max(0, box[1] - 10), min(box[2] + 10, size[0]), min(box[3] + 10, size[1])]
        )
        coordinate.append(
            [max(0, box[0] - 25), max(0, box[1] - 25), min(box[2] + 25, size[0]), min(box[3] + 25, size[1])]
        )

    return image_data, coordinate


if __name__ == "__main__":
    from modelscope.pipelines import pipeline
    from modelscope.utils.constant import Tasks

    image_ori = "./screenshot/screenshot.png"
    image = "./screenshot/screenshot.png"
    parameter = "抖音"
    ocr_detection = pipeline(Tasks.ocr_detection, model="damo/cv_resnet18_ocr-detection-line-level_damo")
    ocr_recognition = pipeline(Tasks.ocr_recognition, model="damo/cv_convnextTiny_ocr-recognition-document_damo")
    iw, ih = Image.open(image).size
    if iw > ih:
        iw, ih = ih, iw
    in_coordinate, out_coordinate = ocr(image_ori, parameter, ocr_detection, ocr_recognition, iw, ih)
    print(f"ocr 计算结果为 {in_coordinate} ,{out_coordinate} ")
