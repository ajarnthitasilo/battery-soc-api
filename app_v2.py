from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import httpx
import re
import numpy as np
import time

app = FastAPI()

# ชุดข้อมูลอ้างอิงความละเอียดสูง (จากโมเดลเก่าที่คุณอาใช้)
# [BVV, SOC] อิงจากระบบ 12 Packs (144 Cells)
REFERENCE_DATA = [
    [470.0, 31.94], [474.2, 45.51], [480.0, 55.83], [483.0, 61.04], 
    [483.9, 62.60], [484.0, 62.78], [484.1, 62.95], [484.2, 63.12], 
    [484.3, 63.30], [490.0, 75.69], [492.0, 79.17]
]
REF_BVV = np.array([p[0] for p in REFERENCE_DATA])
REF_SOC = np.array([p[1] for p in REFERENCE_DATA])

@app.get("/api/data")
async def get_data():
    url = "http://203.150.226.21/jonix/data.php"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with httpx.AsyncClient(headers=headers, timeout=5.0) as client:
            resp = await client.get(url)
            match = re.search(r'BVV["\s:=]+([\d.]+)', resp.text)
            bvv = float(match.group(1)) if match else 484.3
    except:
        bvv = 484.3

    # --- ระบบคำนวณความน่าจะเป็นของ Packs อัตโนมัติ ---
    # หาก BVV ต่ำกว่า 430V ระบบจะวิเคราะห์ว่าเป็น 11 Packs โดยอัตโนมัติ
    detected_packs = 12 if bvv > 430 else 11
    
    # คำนวณ Scaling Factor (11/12 หรือ 12/12)
    scale = detected_packs / 12.0
    
    # ปรับแนวแรงดันอ้างอิงตามจำนวน Pack ที่ตรวจพบ
    adjusted_bvv_axis = REF_BVV * scale
    
    # คำนวณ SOC แบบทศนิยมละเอียด (Linear Interpolation)
    soc = float(np.interp(bvv, adjusted_bvv_axis, REF_SOC))
    
    # แรงดันเฉลี่ยต่อเซลล์
    v_cell = bvv / (detected_packs * 12)
    
    return {
        "bvv": round(bvv, 2),
        "v_cell": round(v_cell, 4),
        "soc": round(soc, 2), # แสดงผลทศนิยม 2 ตำแหน่งตามโมเดลเก่า
        "packs": detected_packs,
        "time": time.strftime("%H:%M:%S"),
        "alert": v_cell < 3.24
    }

@app.get("/v2", response_class=HTMLResponse)
async def read_index():
    with open("dashboard.html", "r") as f:
        return f.read()
