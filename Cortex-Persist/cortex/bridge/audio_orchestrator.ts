/**
 * cortex.bridge/audio_orchestrator.ts
 * ==================================
 * The "Nervous System" of the Triple Engine Architecture.
 * Orchestrates the Control-Rate loop (50-100ms) between DSP and CORTEX.
 */

export interface AudioFeatures {
  rms: number;
  true_peak: number;
  crest_factor: number;
  lufs_short: number;
  high_band_energy: number;
  overs_count: number;
  gain_reduction: number;
}

export interface MasteringPolicy {
  ceiling: number;
  threshold: number;
  ratio: number;
  mix: number;
  drive: number;
}

export class AudioOrchestrator {
  private currentPolicy: MasteringPolicy = {
    ceiling: 0,
    threshold: -2,
    ratio: 2,
    mix: 0.2,
    drive: 0.8
  };

  private targetPolicy: MasteringPolicy = { ...this.currentPolicy };
  private smoothingFactor = 0.15; // Ramping speed (EMA proxy)

  constructor(private pythonApiUrl: string) {}

  /**
   * Main Control Loop (Called from DSP every N blocks or internal timer)
   * This is the "Slow Plan" entrance.
   */
  async pulse(features: AudioFeatures): Promise<MasteringPolicy> {
    try {
      // 1. Send features to Python Brain (Governor v2.2)
      const response = await fetch(`${this.pythonApiUrl}/v1/homeostasis/audio_pulse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...features,
          ts: Date.now() / 1000,
          dt: 0.1, // Fixed control rate for prototype
        })
      });

      if (response.ok) {
        const data = await response.json();
        this.targetPolicy = data.policy;
      }
    } catch (error) {
      console.warn('◈ [CORTEX_BRIDGE_FAULT] Reverting to Safe Policy:', error);
      this.targetPolicy = this.getSafePolicy();
    }

    // 2. Perform Parameter Smoothing (Prevent Zipper Noise)
    this.smoothParameters();

    return this.currentPolicy;
  }

  private smoothParameters() {
    // Basic LERP for all parameters
    const keys: (keyof MasteringPolicy)[] = ['ceiling', 'threshold', 'ratio', 'mix', 'drive'];
    keys.forEach(key => {
      this.currentPolicy[key] += (this.targetPolicy[key] - this.currentPolicy[key]) * this.smoothingFactor;
    });
  }

  private getSafePolicy(): MasteringPolicy {
    return {
      ceiling: -0.5,
      threshold: -12.0,
      ratio: 20.0,
      mix: 1.0,
      drive: 0.0
    };
  }
}
