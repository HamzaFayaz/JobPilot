# Project IGI Game - AimBot-Computer Vision
YOLO v10 ByteTrack Tkinter OpenCV


## 📋 About This Project
An advanced AI-powered aimbot system built with modular architecture for real-time object detection, intelligent tracking, and automated targeting. The project leverages YOLO v10 for high-performance object detection, ByteTrack for smooth multi-object tracking, and a professional GUI interface for seamless control and monitoring.

## What Makes It Special:
- 🎯 **Real-Time Detection**: Ultra-fast YOLO v10 object detection with CUDA acceleration for maximum performance.
- 🔄 **Intelligent Tracking**: ByteTrack algorithm provides smooth, consistent object tracking across frames.
- 🎮 **Professional GUI**: Clean Tkinter interface with real-time controls and status monitoring.
- ⚡ **High Performance**: Optimized for 60+ FPS detection without video preview overhead.
- 🎛️ **Configurable Settings**: Adjustable detection threshold, aim smoothing, and mouse sensitivity.
- 🔧 **Modular Architecture**: Clean separation between detection logic, UI components, and main application.
- 🖱️ **Precise Targeting**: Advanced aiming algorithms with smoothing and sensitivity controls.
- 📊 **Live Monitoring**: Real-time FPS, shot count, and target detection statistics.
- 🛡️ **Thread-Safe Design**: Robust error handling and thread-safe operations for stability.
- 🎯 **Enemy-Focused**: Specialized targeting for enemy objects with distance-based prioritization.

> ## **💡 Special Note**:
This project uses a fully custom dataset that I built entirely from scratch. Every single image was individually collected, annotated, and preprocessed by hand — no pre-made datasets were used. By curating the dataset image by image, I ensured maximum relevance, precision, and quality, which leads to superior model performance compared to relying on generic datasets.

## 🎬 Demo & Screenshots

**Demo 1 Complete Working AimBot Demo**  


https://github.com/user-attachments/assets/9c03c2f2-9c3f-4ac4-9f95-d8db3036da6d


**Demo 2 Enemies Detecion Demo**  

https://github.com/user-attachments/assets/c7cc489d-3bad-4930-b856-fb7c0edcfbb7


**UI Screenshot**  


<img src="https://github.com/user-attachments/assets/7afba2ae-a4ab-475a-9ede-debd6c73fe96" alt="UI image" width="599" height="530" />



## 🚀 Key Features
**Core Functionality**
- 🧠 **AI-Powered Detection**: YOLO v10 neural network for real-time object detection with CUDA acceleration.
- 📂 **Intelligent Tracking**: ByteTrack algorithm for consistent multi-object tracking across frames.
- 🔎 **Smart Targeting**: Distance-based target prioritization with enemy-focused detection.
- 🪄 **Modular Architecture**: Clean separation between detection logic, UI components, and main application.
- ⚡ **High-Performance Processing**: 60+ FPS detection without video preview overhead.
- 📊 **Real-time Monitoring**: Live FPS, shot count, and target detection statistics.
- 🔌 **Seamless Integration**: Built-in support for win32api mouse control and screen capture.

**GUI Features**
- 🎨 **Professional Interface**: Modern Tkinter GUI with clean, intuitive design.
- 📱 **Responsive Controls**: Real-time button states and status indicators.
- 📂 **Live Statistics**: Real-time FPS, shot count, and target monitoring display.
- 💬 **Status Updates**: Live detection status and target count information.
- 🔄 **Dynamic Controls**: Toggle buttons for aim and target lock with visual feedback.
- 🧩 **Settings Panel**: Sliders for detection threshold, aim smoothing, and mouse sensitivity.

**Detection Features**
- ⚡ **YOLO v10 Engine**: State-of-the-art object detection with CUDA support.
- 🪄 **ByteTrack Integration**: Advanced multi-object tracking for consistent target following.
- 📂 **Screen Capture**: High-performance MSS-based screen grabbing.
- 🧠 **Aimbot Logic**: Intelligent aiming algorithms with smoothing and sensitivity controls.
- 🔄 **Timer-Based Processing**: Optimized detection loop for maximum performance.
- 📜 **Error Handling**: Robust error management and recovery mechanisms.
- 🐳 **Cross-Platform Ready**: Windows-optimized with professional deployment structure.

## 🏗️ Architecture
```
Project IGI Game/
├── main.py              # Application entry point with dependency checking
├── detector.py          # Core detection and aimbot logic
├── ui.py               # Professional Tkinter GUI interface
├── Models/
│   └── best.pt         # YOLO v10 model file
├── requirements.txt    # Python dependencies
└── README.md          # Project documentation
```

## 📊 Dataset & Model Downloads
**Training Dataset**
- **Dataset Download**: [Download Dataset](https://universe.roboflow.com/computer-vison-fznpi/project-igi-1/dataset/6)
- **Dataset Format**: YOLO format with bounding box annotations
- **Classes**: Enemy objects and game entities

**Pre-trained Model**
- **Model Download**: [Download best.pt](https://drive.google.com/file/d/1Xpr1o3PK_u2G-SUtVbzP2FNTn9wCpSk3/view?usp=sharing)

## 🔧 Troubleshooting & Debugging
**If you encounter any issues with the application, refer to the development notebooks:**

### **Development Notebooks**
- **`temp.ipynb`**: Contains experimental code and testing scripts
- **`Experiment.ipynb`**: Contains the original development code without UI components

### **Debugging Steps**
1. **Check the notebooks** for working examples of the core detection logic
2. **Compare implementations** between the notebooks and the main application files
3. **Test individual components** using the notebook code as reference
4. **Verify model loading** and detection pipeline using the experimental code

### **Common Issues**
- **Model loading errors**: Check `Experiment.ipynb` for proper model initialization
- **Detection problems**: Refer to `temp.ipynb` for detection parameter tuning
- **Performance issues**: Use notebook code to benchmark individual components
- **Dependency conflicts**: Test with the exact versions used in the notebooks

> **💡 Tip**: The notebooks contain the original working code without UI overhead, making them perfect for debugging core functionality issues.

## 🛠️ Installation
1. **Prerequisites**: Python 3.8+, Windows 10/11
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Model Setup**: Ensure `best.pt` is in the `Models/` folder
4. **Run Application**:
   ```bash
   python main.py
   ```

## 🎮 Usage
1. **Launch**: Start the application with `python main.py`
2. **Configure**: Adjust detection threshold, aim smoothing, and mouse sensitivity
3. **Start Detection**: Click "Start Detection" to begin real-time monitoring
4. **Enable Aimbot**: Toggle "Aim" and "Target Lock" for automated targeting
5. **Monitor**: Watch real-time stats for FPS, shots fired, and targets detected

## ⚙️ Configuration
- **Detection Threshold**: 0.1 - 1.0 (confidence level for object detection)
- **Aim Smoothing**: 0.1 - 1.0 (smoothness of mouse movement)
- **Mouse Sensitivity**: 0.1 - 2.0 (aiming responsiveness)
- **Target Lock**: Automatic shooting when target is within threshold
- **Aim Mode**: Manual or automatic targeting system

## 🔧 Technical Details
- **Detection Engine**: YOLO v10 with CUDA acceleration
- **Tracking Algorithm**: ByteTrack for multi-object tracking
- **GUI Framework**: Tkinter with modern styling
- **Screen Capture**: MSS for high-performance screen grabbing
- **Mouse Control**: win32api for precise mouse movement
- **Threading**: Timer-based detection loop for optimal performance

## 📊 Performance
- **Detection Speed**: 60+ FPS on modern hardware
- **Latency**: < 16ms per detection cycle
- **Memory Usage**: Optimized for minimal RAM consumption
- **CPU Usage**: Efficient processing without video overhead
- **GPU Acceleration**: CUDA support for faster detection

## 🎯 Target Detection
- **Object Classes**: Configurable YOLO model classes
- **Enemy Targeting**: Specialized detection for enemy objects
- **Distance Calculation**: Euclidean distance-based target prioritization
- **Tracking IDs**: Persistent object identification across frames
- **Confidence Filtering**: Threshold-based detection filtering

## 🛡️ Safety & Ethics
- **Educational Purpose**: Designed for learning and research
- **Responsible Use**: Ensure compliance with game terms of service
- **Ethical Guidelines**: Use responsibly and ethically
- **Legal Compliance**: Respect applicable laws and regulations

## 🔄 Updates & Maintenance
- **Modular Design**: Easy to extend and modify
- **Clean Code**: Well-documented and maintainable
- **Error Handling**: Robust error management and recovery
- **Performance Monitoring**: Built-in FPS and statistics tracking


## ⚠️ Disclaimer

This project is for educational and research purposes only. Users are responsible for ensuring compliance with applicable laws, game terms of service, and ethical guidelines. The developers are not responsible for any misuse of this software.







