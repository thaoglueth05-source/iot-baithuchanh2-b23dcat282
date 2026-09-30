# BÀI THỰC HÀNH SỐ 2: THU THẬP, LƯU TRỮ VÀ TIỀN XỬ LÝ DỮ LIỆU IoT
* **Học phần:** IoT và Ứng dụng (INT14149)
* **Họ và tên:** Trần Phương Thảo
* **Mã sinh viên:** B23DCAT282
* **Nhóm:** 14
* **Giảng viên hướng dẫn:** TS. Nguyễn Tài Tuyên

##  1. Tổng quan

Dự án xây dựng một pipeline hoàn chỉnh thu thập dữ liệu thời gian thực từ cảm biến môi trường mô phỏng trên ESP32 (Wokwi), truyền qua giao thức MQTT đến InfluxDB Cloud, thực hiện tiền xử lý dữ liệu (làm sạch, lọc bất thường, resampling, chuẩn hóa Z-score) và hiển thị trực quan trên Streamlit Dashboard.

##  2. Kiến trúc hệ thống

+---------------------+        MQTT Publish         +----------------------+
|   ESP32 Sensor      | --------------------------> | HiveMQ Public Broker |
| (DHT22 + HC-SR04)   | (sensors/esp32_01/telemetry)| (broker.hivemq.com)  |
+---------------------+                             +----------------------+
                                                               |
                                                          MQTT Subscribe
                                                               v
+---------------------+       Read/Write Data       +----------------------+
| Streamlit Dashboard | <-------------------------- |  Python Client App   |
|  (Monitoring UI)    |                             | (Collector & Clean)  |
+---------------------+                             +----------------------+
                                                               |
                                                          Flux Queries
                                                               v
                                                    +----------------------+
                                                    |    InfluxDB Cloud    |
                                                    | (iot_raw/iot_clean)  |
                                                    +----------------------+


##  3. Cấu trúc thư mục dự án

.
├── firmware/
│   ├── sketch.ino            # Mã nguồn C++ cho ESP32 trên Wokwi
│   └── libraries.txt         # Danh sách thư viện C++ sử dụng trên Wokwi
├── scripts/
│   ├── mqtt_to_influx.py     # Script thu thập dữ liệu MQTT ghi vào InfluxDB (iot_raw)
│   ├── preprocess_pipeline.py# Script tiền xử lý dữ liệu và ghi vào InfluxDB (iot_cleaned)
│   └── app.py                # Dashboard giám sát thời gian thực bằng Streamlit
├── config/
│   ├── diagram.json          # Sơ đồ kết nối phần cứng Wokwi
│   └── requirements.txt      # Danh sách thư viện Python cần cài đặt
├── .gitignore                # Ẩn các file tạm và cấu hình môi trường
└── README.md                 # Tài liệu hướng dẫn chạy bài thực hành

##  4. Hướng dẫn cài đặt và khởi chạy

### Bước 1: Khởi chạy phần cứng mô phỏng (Wokwi)

1. Mở dự án trên [Wokwi](https://wokwi.com/).
2. Tải code trong `firmware/sketch.ino` và tệp `config/diagram.json` lên dự án.
3. Bấm **Play** để bắt đầu phát dữ liệu telemetry lên Broker `broker.hivemq.com`.

### Bước 2: Cài đặt môi trường Python: Mở Terminal tại thư mục gốc dự án và chạy lệnh: pip install -r config/requirements.txt

### Bước 3: Chạy ứng dụng thu thập và xử lý

1. **Mở Terminal 1 - Thu thập dữ liệu từ MQTT sang InfluxDB:** python scripts/mqtt_to_influx.py

2. **Mở Terminal 2 - Chạy Pipeline tiền xử lý dữ liệu:** python scripts/preprocess_pipeline.py

3. **Mở Terminal 3 - Khởi chạy Dashboard giám sát:** streamlit run scripts/app.py

##  5. Tính năng chính của Dashboard Streamlit

* **Real-time Raw Data Tab:** Hiển thị chỉ số nhiệt độ, độ ẩm, khoảng cách hiện tại cùng biểu đồ biến thiên dữ liệu thô từ bucket `iot_raw`.
* **Preprocessed Data Tab:** So sánh biểu đồ nhiệt độ gốc với nhiệt độ trung bình trượt (Rolling Mean) và xem bảng dữ liệu đã xử lý từ bucket `iot_cleaned`.
