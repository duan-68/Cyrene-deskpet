import os
import numpy as np
from PIL import Image

im = Image.open(r"E:\code\picture\rubbish_bin.png").convert("RGBA")
a = np.array(im)

# 主体范围（区域19 的 bbox），避免边缘噪点
X0, X1 = 321, 663
SPLIT = 225  # 盖子和桶体分界

lid = a[80:SPLIT, X0:X1].copy()      # 盖子（含提手+盖板）
body = a[SPLIT:530, X0:X1].copy()    # 桶体

def trim(img_arr):
    alpha = img_arr[..., 3] > 10
    rows = np.where(alpha.any(axis=1))[0]
    cols = np.where(alpha.any(axis=0))[0]
    if len(rows) == 0 or len(cols) == 0:
        return img_arr
    return img_arr[rows.min():rows.max()+1, cols.min():cols.max()+1]

lid = trim(lid)
body = trim(body)

out = "web"
Image.fromarray(lid, "RGBA").save(os.path.join(out, "bin_lid.png"))
Image.fromarray(body, "RGBA").save(os.path.join(out, "bin_body.png"))
print("盖子 lid:", Image.fromarray(lid).size)
print("桶体 body:", Image.fromarray(body).size)
