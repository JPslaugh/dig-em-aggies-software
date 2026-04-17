// Actuators
#ifndef ACTUATORS_HPP
#define ACTUATORS_HPP

#include "base.hpp"
#include <algorithm>
#include <cmath>

// Motor controller base
class MotorController : public IActuator {
protected:
    std::string name_;
    double commandValue_;
    double feedbackValue_;
    double minLimit_;
    double maxLimit_;
    bool interlockActive_;
    bool enabled_;

public:
    MotorController(const std::string& name, double minLim, double maxLim)
        : name_(name), commandValue_(0.0), feedbackValue_(0.0),
          minLimit_(minLim), maxLimit_(maxLim), 
          interlockActive_(false), enabled_(false) {}

    bool initialize() override {
        enabled_ = true;
        commandValue_ = 0.0;
        return true;
    }

    bool update() override {
        if (!enabled_ || interlockActive_) {
            commandValue_ = 0.0;
            return false;
        }
        // Update feedback from hardware
        return true;
    }

    bool shutdown() override {
        commandValue_ = 0.0;
        enabled_ = false;
        return true;
    }

    bool setCommand(double value) override {
        if (!enabled_ || interlockActive_) return false;
        
        commandValue_ = std::clamp(value, minLimit_, maxLimit_);
        return true;
    }

    double getCommand() const override { return commandValue_; }
    double getFeedback() const override { return feedbackValue_; }
    bool hasInterlock() const override { return interlockActive_; }
    
    void setInterlock(bool active) { interlockActive_ = active; }
    
    std::string getStatus() const override {
        return name_ + ": Cmd = " + std::to_string(commandValue_) + 
               " FB = " + std::to_string(feedbackValue_);
    }
    
    std::string getComponentName() const override { return name_; }
};

class ThrusterMotor : public MotorController {
public:
    ThrusterMotor(const std::string& name) 
        : MotorController(name, -100.0, 100.0) {} // -100% to +100%
};

class HydraulicValve : public IActuator {
private:
    std::string name_;
    double position_; // 0-100%
    double targetPosition_;
    bool interlockActive_;
    
public:
    HydraulicValve(const std::string& name)
        : name_(name), position_(0.0), targetPosition_(0.0),
          interlockActive_(false) {}

    bool initialize() override { position_ = 0.0; return true; }
    
    bool update() override {
        if (interlockActive_) {
            targetPosition_ = 0.0;
            return false;
        }
        // Simulate gradual movement
        double error = targetPosition_ - position_;
        position_ += std::clamp(error, -5.0, 5.0); // 5% per update
        return true;
    }

    bool shutdown() override { 
        targetPosition_ = 0.0;
        position_ = 0.0;
        return true; 
    }

    bool setCommand(double value) override {
        if (interlockActive_) return false;
        targetPosition_ = std::clamp(value, 0.0, 100.0);
        return true;
    }

    double getCommand() const override { return targetPosition_; }
    double getFeedback() const override { return position_; }
    bool hasInterlock() const override { return interlockActive_; }
    
    void setInterlock(bool active) { interlockActive_ = active; }
    
    std::string getStatus() const override {
        return name_ + ": Pos=" + std::to_string(position_) + "%";
    }
    
    std::string getComponentName() const override { return name_; }
};

#endif