import os
from PIL import Image, ImageDraw, ImageFont

WORKSPACE_ROOT = r"d:\~Ideas n Innovation\~~Taiwan\AU\11_Task_Robotic\kuka_ros2"
IMAGES_DIR = os.path.join(WORKSPACE_ROOT, "images")

def create_figure2_composite():
    frame_path = os.path.join(IMAGES_DIR, "frame.png")
    aruco_path = os.path.join(IMAGES_DIR, "aruco_debug.png")
    out_path = os.path.join(IMAGES_DIR, "figure2_aruco_side_by_side.png")

    img1 = Image.open(frame_path).convert("RGB")
    img2 = Image.open(aruco_path).convert("RGB")

    # Match heights
    target_height = 900
    w1 = int(img1.width * (target_height / img1.height))
    img1_resized = img1.resize((w1, target_height), Image.Resampling.LANCZOS)

    w2 = int(img2.width * (target_height / img2.height))
    img2_resized = img2.resize((w2, target_height), Image.Resampling.LANCZOS)

    spacing = 30
    banner_height = 60
    total_width = w1 + w2 + spacing
    total_height = target_height + banner_height

    composite = Image.new("RGB", (total_width, total_height), (255, 255, 255))
    composite.paste(img1_resized, (0, 0))
    composite.paste(img2_resized, (w1 + spacing, 0))

    draw = ImageDraw.Draw(composite)
    # Try default or standard font
    try:
        font = ImageFont.truetype("arial.ttf", 32)
    except Exception:
        font = ImageFont.load_default()

    draw.text((w1 // 2 - 180, target_height + 12), "(a) Raw Workspace Camera Frame", fill=(20, 20, 20), font=font)
    draw.text((w1 + spacing + w2 // 2 - 240, target_height + 12), "(b) ArUco Constellation & Color Segmentation", fill=(20, 20, 20), font=font)

    composite.save(out_path, dpi=(300, 300))
    print(f"Successfully generated Figure 2 composite at: {out_path}")

if __name__ == "__main__":
    create_figure2_composite()
