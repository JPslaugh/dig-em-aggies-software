// ECU
#ifndef ECU_HPP
#define ECU_HPP

#include "base.hpp"
#include <vector>
#include <map>
#include <memory>
#include <string>
#include <iomanip>
#include <sstream>

// ECU Types enumeration
enum class ECUType {
    MAIN_CONTROLLER,      // Raspberry Pi
    SENSOR_NODE,          // Teensy - Sensors
    ACTUATOR_NODE,        // Teensy - Actuators
    VFD_CONTROLLER,       // Variable Frequency Drive
    HYDRAULIC_CONTROLLER, // Hydraulic system controller
    CUSTOM                // For future expansion
};

// ECU Status enumeration
enum class ECUStatus {
    OFFLINE,
    INITIALIZING,
    ONLINE,
    FAULT,
    DEGRADED
};

// ECU Location information
struct ECULocation {
    std::string compartment;      // e.g., "Main Electronics Bay"
    std::string mounting;         // e.g., "DIN Rail", "Panel Mount"
    double x_position;            // Position in meters from reference
    double y_position;
    double z_position;
};

// What the ECU controls
struct ControlledDevice {
    std::string deviceName;       // e.g., "Forward Thruster"
    std::string deviceType;       // e.g., "Motor", "Valve", "Sensor"
    std::string interface;        // e.g., "PWM", "Modbus", "I2C"
    int channelNumber;            // Physical channel/pin
};

// Communication details
struct CommunicationInfo {
    std::string protocol;         // "Serial", "Ethernet", "Modbus RTU", etc.
    std::string address;          // "/dev/ttyACM0", "192.168.1.50", etc.
    int baudRate;                 // For serial
    int modbusAddress;            // For Modbus devices
    double updateRateHz;          // How often this ECU is polled/updates
};

// ECU Class - Represents one Electronic Control Unit
class ECU : public ISystemComponent {
private:
    std::string ecuID_;
    std::string name_;
    ECUType type_;
    ECUStatus status_;
    ECULocation location_;
    CommunicationInfo commInfo_;
    std::vector<ControlledDevice> controlledDevices_;
    
    // Health monitoring
    std::chrono::system_clock::time_point lastCommunication_;
    double cpuUsagePercent_;
    double memoryUsagePercent_;
    double temperatureCelsius_;
    int communicationErrors_;
    bool watchdogActive_;

public:
    ECU(const std::string& ecuID, const std::string& name, ECUType type)
        : ecuID_(ecuID), name_(name), type_(type), 
          status_(ECUStatus::OFFLINE),
          cpuUsagePercent_(0.0), memoryUsagePercent_(0.0),
          temperatureCelsius_(0.0), communicationErrors_(0),
          watchdogActive_(false) {
        
        lastCommunication_ = std::chrono::system_clock::now();
    }

    // ISystemComponent implementation
    bool initialize() override {
        status_ = ECUStatus::INITIALIZING;
        communicationErrors_ = 0;
        
        // Attempt to establish communication
        bool commSuccess = establishCommunication();
        
        if (commSuccess) {
            status_ = ECUStatus::ONLINE;
            watchdogActive_ = true;
            return true;
        } else {
            status_ = ECUStatus::FAULT;
            return false;
        }
    }

    bool update() override {
        // Check watchdog timeout
        auto now = std::chrono::system_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(
            now - lastCommunication_);
        
        if (elapsed.count() > 5 && status_ == ECUStatus::ONLINE) {
            status_ = ECUStatus::DEGRADED;
            communicationErrors_++;
        }
        
        // Update health metrics (placeholder - would read from actual ECU)
        updateHealthMetrics();
        
        return status_ == ECUStatus::ONLINE || status_ == ECUStatus::DEGRADED;
    }

    bool shutdown() override {
        status_ = ECUStatus::OFFLINE;
        watchdogActive_ = false;
        return true;
    }
    // Jay was here ;D
    std::string getStatus() const override {
        std::stringstream ss;
        ss << name_ << " [" << ecuID_ << "]: " << statusToString(status_);
        ss << " | Errors: " << communicationErrors_;
        ss << " | Temp: " << std::fixed << std::setprecision(1) 
           << temperatureCelsius_ << "°C";
        return ss.str();
    }

    std::string getComponentName() const override {
        return name_;
    }

    // ECU-specific methods
    void setLocation(const ECULocation& location) {
        location_ = location;
    }

    void setCommunication(const CommunicationInfo& commInfo) {
        commInfo_ = commInfo;
    }

    void addControlledDevice(const ControlledDevice& device) {
        controlledDevices_.push_back(device);
    }

    void updateCommunicationTimestamp() {
        lastCommunication_ = std::chrono::system_clock::now();
        if (status_ == ECUStatus::DEGRADED) {
            status_ = ECUStatus::ONLINE;
        }
    }

    // Getters
    std::string getECUID() const { return ecuID_; }
    ECUType getType() const { return type_; }
    ECUStatus getECUStatus() const { return status_; }
    ECULocation getLocation() const { return location_; }
    CommunicationInfo getCommunicationInfo() const { return commInfo_; }
    const std::vector<ControlledDevice>& getControlledDevices() const {
        return controlledDevices_;
    }
    
    double getCPUUsage() const { return cpuUsagePercent_; }
    double getMemoryUsage() const { return memoryUsagePercent_; }
    double getTemperature() const { return temperatureCelsius_; }
    int getCommunicationErrors() const { return communicationErrors_; }

    // Generate detailed report for documentation
    std::string generateReport() const {
        std::stringstream ss;
        
        ss << "╔════════════════════════════════════════════════════════╗\n";
        ss << "║ ECU: " << std::left << std::setw(47) << name_ << "║\n";
        ss << "╠════════════════════════════════════════════════════════╣\n";
        ss << "║ ID:       " << std::setw(44) << ecuID_ << "║\n";
        ss << "║ Type:     " << std::setw(44) << typeToString(type_) << "║\n";
        ss << "║ Status:   " << std::setw(44) << statusToString(status_) << "║\n";
        ss << "╠════════════════════════════════════════════════════════╣\n";
        ss << "║ LOCATION                                               ║\n";
        ss << "║   Compartment: " << std::setw(39) << location_.compartment << "║\n";
        ss << "║   Mounting:    " << std::setw(39) << location_.mounting << "║\n";
        ss << "║   Position:    X=" << std::fixed << std::setprecision(2) 
           << location_.x_position << "m Y=" << location_.y_position 
           << "m Z=" << location_.z_position << "m" << std::setw(10) << "" << "║\n";
        ss << "╠════════════════════════════════════════════════════════╣\n";
        ss << "║ COMMUNICATION                                          ║\n";
        ss << "║   Protocol:    " << std::setw(39) << commInfo_.protocol << "║\n";
        ss << "║   Address:     " << std::setw(39) << commInfo_.address << "║\n";
        
        if (commInfo_.baudRate > 0) {
            ss << "║   Baud Rate:   " << std::setw(39) << commInfo_.baudRate << "║\n";
        }
        if (commInfo_.modbusAddress > 0) {
            ss << "║   Modbus Addr: " << std::setw(39) << commInfo_.modbusAddress << "║\n";
        }
        ss << "║   Update Rate: " << std::setw(36) << commInfo_.updateRateHz 
           << " Hz" << "║\n";
        ss << "╠════════════════════════════════════════════════════════╣\n";
        ss << "║ CONTROLLED DEVICES (" << controlledDevices_.size() << ")";
        ss << std::setw(33 - std::to_string(controlledDevices_.size()).length()) 
           << "" << "║\n";
        
        for (const auto& device : controlledDevices_) {
            ss << "║   • " << std::setw(50) << device.deviceName << "║\n";
            ss << "║     Type: " << std::setw(26) << device.deviceType 
               << " Interface: " << std::setw(10) << device.interface << "║\n";
            ss << "║     Channel: " << std::setw(41) << device.channelNumber << "║\n";
        }
        
        ss << "╠════════════════════════════════════════════════════════╣\n";
        ss << "║ HEALTH METRICS                                         ║\n";
        ss << "║   CPU Usage:    " << std::setw(34) << std::fixed 
           << std::setprecision(1) << cpuUsagePercent_ << " %" << "║\n";
        ss << "║   Memory Usage: " << std::setw(34) << memoryUsagePercent_ << " %" << "║\n";
        ss << "║   Temperature:  " << std::setw(34) << temperatureCelsius_ << " °C" << "║\n";
        ss << "║   Comm Errors:  " << std::setw(38) << communicationErrors_ << "║\n";
        ss << "╚════════════════════════════════════════════════════════╝\n";
        
        return ss.str();
    }

private:
    bool establishCommunication() {
        // Placeholder for actual communication establishment
        // In real implementation:
        // - Open serial port
        // - Establish TCP connection
        // - Initialize Modbus
        // - Verify ECU responds
        return true;
    }

    void updateHealthMetrics() {
        // Placeholder - in real implementation would query ECU
        // For Raspberry Pi: read /proc/stat, /proc/meminfo, thermal zone
        // For Teensy: request status packet
        // For VFD: read Modbus registers
        
        // Simulate some values
        cpuUsagePercent_ = 25.0;
        memoryUsagePercent_ = 40.0;
        temperatureCelsius_ = 45.0;
    }

    std::string typeToString(ECUType type) const {
        switch (type) {
            case ECUType::MAIN_CONTROLLER: return "Main Controller (Raspberry Pi)";
            case ECUType::SENSOR_NODE: return "Sensor Node (Teensy)";
            case ECUType::ACTUATOR_NODE: return "Actuator Node (Teensy)";
            case ECUType::VFD_CONTROLLER: return "VFD Controller";
            case ECUType::HYDRAULIC_CONTROLLER: return "Hydraulic Controller";
            case ECUType::CUSTOM: return "Custom ECU";
            default: return "Unknown";
        }
    }

    std::string statusToString(ECUStatus status) const {
        switch (status) {
            case ECUStatus::OFFLINE: return "OFFLINE";
            case ECUStatus::INITIALIZING: return "INITIALIZING";
            case ECUStatus::ONLINE: return "ONLINE";
            case ECUStatus::FAULT: return "FAULT";
            case ECUStatus::DEGRADED: return "DEGRADED";
            default: return "UNKNOWN";
        }
    }
};

#endif // ECU_HPP