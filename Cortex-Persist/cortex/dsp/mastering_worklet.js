/**
 * cortex.dsp/mastering_worklet.js
 * =============================
 * The "Muscle" of the Triple Engine Architecture.
 * Sample-Accurate Peak Limiter & Processor.
 * 
 * Runs in the AudioWorklet thread (Fast Plane).
 */

class MasteringWorkletProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.port.onmessage = (event) => {
      this.handleCommand(event.data);
    };

    // State
    this.params = {
      ceiling: 0.0,
      threshold: -2.0,
      ratio: 2.0,
      mix: 0.2,
      drive: 0.8
    };
    
    // Emergency State
    this.isEvasionActive = false;
  }

  handleCommand(data) {
    if (data.type === 'UPDATE_PARAMS') {
      this.params = data.params;
    }
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    const output = outputs[0];

    // Standard block size: 128 samples
    for (let channel = 0; channel < input.length; ++channel) {
      const inputChannel = input[channel];
      const outputChannel = output[channel];
      
      for (let i = 0; i < inputChannel.length; ++i) {
        let sample = inputChannel[i];
        
        // 1. Process Audio (Placeholder: Simplified Drive + Limit)
        sample = this.applyDrive(sample, this.params.drive);
        sample = this.applyLimiter(sample, this.params.ceiling);
        
        // 2. Emergency Peak Guard (Fast Plane Reflector)
        if (Math.abs(sample) > 1.0) {
           sample = Math.sign(sample); // Hard Clip Guard
        }

        outputChannel[i] = sample;
      }
    }

    return true;
  }

  applyDrive(s, d) {
    // Basic soft-clipper drive
    return Math.tanh(s * (1.0 + d * 5));
  }

  applyLimiter(s, ceil) {
    // Simple brick-wall placeholder
    const limit = Math.pow(10, ceil / 20);
    return Math.max(-limit, Math.min(limit, s));
  }
}

registerProcessor('mastering-worklet-v2', MasteringWorkletProcessor);
