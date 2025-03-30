# server.py
import random
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/data", methods=["GET"])
def get_data():
    """
    Возвращает pseudo-датасет:
    {
      "data": [список чисел],
      "labels": [0/1 метки, если хотим],
    }
    Шанс аномалии ~ 7% в среднем
    """
    n = int(request.args.get("n", 10))  # сколько точек вернуть
    anomaly_rate = float(request.args.get("rate", 0.07))

    data = []
    labels = []
    for _ in range(n):
        val = random.gauss(50, 7)  # нормальное со средним 50 и sigma=7
        is_anomaly = False
        if random.random() < anomaly_rate:
            # разные типы аномалий
            anomaly_type = random.choice(["big_pos", "big_neg", "zero"])
            if anomaly_type == "big_pos":
                val += random.uniform(70, 120)
            elif anomaly_type == "big_neg":
                val -= random.uniform(50, 100)
            else:  # zero
                val = 0
            is_anomaly = True
        data.append(val)
        labels.append(1 if is_anomaly else 0)

    return jsonify({"data": data, "labels": labels})

@app.route("/detect", methods=["POST"])
def detect_anomalies():
    """
    Примитивная логика (псевдомодель на сервере):
    - Если число < 10 или > 90, считаем аномалией
    - Возвращаем JSON вида: { \"results\": [0/1, ...] }
    """
    content = request.json
    if not content or "values" not in content:
        return jsonify({"error": "No 'values' field in JSON"}), 400

    values = content["values"]
    results = []
    for x in values:
        # Простая логика
        if x < 10 or x > 90:
            results.append(1)  # anomaly
        else:
            results.append(0)  # normal

    return jsonify({"results": results})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
