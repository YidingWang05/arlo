import time
from app.schemas.m4_frame import FamilyPhotoPush, FramePhotoItem

FRAME_ALBUM = [
    FramePhotoItem(
        id="1",
        image_url="https://images.unsplash.com/photo-1511895426328-dc8714191300?w=800",
        caption="Family Mid-Autumn Festival Gathering",
        timestamp="2026-10-01"
    )
]

async def push_family_photo(item: FamilyPhotoPush) -> bool:
    new_photo = FramePhotoItem(
        id=str(int(time.time())),
        image_url=item.image_url,
        caption=f"{item.sender_name}: {item.caption}",
        timestamp="Just now"
    )
    FRAME_ALBUM.insert(0, new_photo)
    return True

async def get_frame_photos() -> list[FramePhotoItem]:
    return FRAME_ALBUM
