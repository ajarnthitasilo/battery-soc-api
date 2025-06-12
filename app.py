from flask import Flask, request, jsonify

app = Flask(__name__)

def estimate_soc(cell_voltage):
    soc_table = {
        3.11: 5,
        3.19: 10,
        3.23: 20,
        3.26: 30,
        3.27: 35,
        3.28: 40,
        3.29: 45,
        3.32: 50,
        3.33: 55,
        3.35: 60,
        3.37: 65,
        3.38: 70,
        3.40: 75,
        3.42: 80,
        3.44: 85,
        3.46: 90,
        3.48: 95,
        3.51: 100
    }

    voltages = sorted(soc_table.keys())
    if cell_voltage <= voltages[0]:
        return 0
    elif cell_voltage >= voltages[-1]:
        return 100

    for i in range(1, len(voltages)):
        if cell_voltage < voltages[i]:
            v1, v2 = voltages[i-1], voltages[i]
            soc1, soc2 = soc_table[v1], soc_table[v2]
            soc = soc1 + (cell_voltage - v1) * (soc2 - soc1) / (v2 - v1)
            return round(soc, 2)
    return None

@app.route("/soc", methods=["POST"])
def calculate_soc():
    data = request.get_json()
    bvv = data.get("bvv")
    if not isinstance(bvv, (int, float)):
        return jsonify({"error": "Invalid input"}), 400
    
    total_cells = 12 * 12
    cell_voltage = bvv / total_cells
    soc = estimate_soc(cell_voltage)

    return jsonify({
        "bvv": bvv,
        "cell_voltage": round(cell_voltage, 3),
        "soc_percent": soc
    })

@app.route("/")
def home():
    return "Battery SOC API is running ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

