export class SonicService {
  private ctx: AudioContext | null = null;
  private droneOsc: OscillatorNode | null = null;
  private droneGain: GainNode | null = null;
  private lpf: BiquadFilterNode | null = null;

  init() {
    if (this.ctx) return;
    this.ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    
    // Ambient Drone (Low Freq Tension)
    this.droneOsc = this.ctx.createOscillator();
    this.droneGain = this.ctx.createGain();
    this.lpf = this.ctx.createBiquadFilter();
    
    this.droneOsc.type = 'sawtooth';
    this.droneOsc.frequency.setValueAtTime(32.7, this.ctx.currentTime); // C1
    
    this.lpf.type = 'lowpass';
    this.lpf.frequency.setValueAtTime(120, this.ctx.currentTime);
    
    this.droneGain.gain.setValueAtTime(0.02, this.ctx.currentTime);
    
    this.droneOsc.connect(this.lpf);
    this.lpf.connect(this.droneGain);
    this.droneGain.connect(this.ctx.destination);
    
    this.droneOsc.start();
  }

  playClick(type: 'hover' | 'deploy' | 'error' | 'proximity' | 'strike') {
    if (!this.ctx) return;
    const osc = this.ctx.createOscillator();
    const g = this.ctx.createGain();
    
    if (type === 'hover') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(800, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(100, this.ctx.currentTime + 0.05);
      g.gain.setValueAtTime(0.03, this.ctx.currentTime);
    } else if (type === 'deploy') {
      osc.type = 'square';
      osc.frequency.setValueAtTime(400, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(800, this.ctx.currentTime + 0.15);
      g.gain.setValueAtTime(0.05, this.ctx.currentTime);
    } else if (type === 'proximity') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(200, this.ctx.currentTime);
      osc.frequency.linearRampToValueAtTime(50, this.ctx.currentTime + 0.1);
      g.gain.setValueAtTime(0.08, this.ctx.currentTime);
    } else if (type === 'strike') {
      osc.type = 'square';
      osc.frequency.setValueAtTime(150, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(10, this.ctx.currentTime + 0.3);
      g.gain.setValueAtTime(0.12, this.ctx.currentTime);
    }
    
    g.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.2);
    
    osc.connect(g);
    g.connect(this.ctx.destination);
    
    osc.start();
    osc.stop(this.ctx.currentTime + 0.2);
  }

  updateDrone(frequency: number, entropy: number) {
    if (!this.droneOsc || !this.lpf || !this.ctx) return;
    
    // Base frequency modulation
    this.droneOsc.frequency.setTargetAtTime(frequency, this.ctx.currentTime, 0.5);
    
    // Tension modulation (Filter Cutoff)
    // Range: 120Hz (calm) to 2000Hz (critical)
    const cutoff = 120 + (entropy / 100) * 1880;
    this.lpf.frequency.setTargetAtTime(cutoff, this.ctx.currentTime, 0.2);
    
    // Volume scaling with stress
    const gainVal = 0.02 + (entropy / 100) * 0.05;
    this.droneGain?.gain.setTargetAtTime(gainVal, this.ctx.currentTime, 0.5);
  }
}

export const sonic = new SonicService();
