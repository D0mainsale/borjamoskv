// ouroboros_stagnation_fsm_v2.sv - Direct-Silicon JIT
// Synthesis Target: O(1) Semantic Drift Analysis via Hamming Distance Popcount
// Enforces Law Ω2 y Ω9: Purging Python Exact-Match Loop into HDC C5-REAL Hardware.

module ouroboros_stagnation_fsm #(
    parameter HASH_WIDTH = 256,
    parameter HISTORY_DEPTH = 4,
    parameter DRIFT_THRESHOLD = 32 // Hamming distances below this indicate semantic stagnation
)(
    input  logic                      clk,
    input  logic                      rst_n,
    input  logic                      eval_enable,
    input  logic [HASH_WIDTH-1:0]     current_gen_vector, // VSA/SDM HDC Vector
    input  logic [HASH_WIDTH-1:0]     gen_history [0:HISTORY_DEPTH-1],
    input  logic [31:0]               convergence_threshold, // Fixed point score
    input  logic [31:0]               current_score,

    output logic                      cmd_converged,
    output logic                      cmd_abort,
    output logic [2:0]                cmd_rotate_persona, // 0=None, 1=Hacker, 2=Contrarian...
    output logic                      c5_hardware_lock
);

    // ==========================================
    // PIPELINE STAGE 1: Semantic Drift XOR Array
    // ==========================================
    logic [HASH_WIDTH-1:0] drift_vector_osc;
    logic [HASH_WIDTH-1:0] drift_vector_prev;

    // We compute drift against Generation (N-2) for oscillation, and (N-1) for diminishing checks.
    assign drift_vector_osc  = current_gen_vector ^ gen_history[1];
    assign drift_vector_prev = current_gen_vector ^ gen_history[0];

    // Pipeline registers for Fmax
    logic [HASH_WIDTH-1:0] drift_vector_osc_reg;
    logic [HASH_WIDTH-1:0] drift_vector_prev_reg;
    logic [31:0]           current_score_reg;
    logic                  eval_enable_reg;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            drift_vector_osc_reg  <= '0;
            drift_vector_prev_reg <= '0;
            current_score_reg     <= '0;
            eval_enable_reg       <= 1'b0;
        end else begin
            drift_vector_osc_reg  <= drift_vector_osc;
            drift_vector_prev_reg <= drift_vector_prev;
            current_score_reg     <= current_score;
            eval_enable_reg       <= eval_enable;
        end
    end

    // ==========================================
    // PIPELINE STAGE 2: Popcount Adder Tree
    // ==========================================
    logic [15:0] hamming_dist_osc;
    logic [15:0] hamming_dist_prev;
    logic        is_oscillating;
    logic        is_diminishing;

    always_comb begin
        // Synthesizable $countones for Wallace/Dadda adder tree instantiation (O(1) in hardware)
        hamming_dist_osc  = $countones(drift_vector_osc_reg);
        hamming_dist_prev = $countones(drift_vector_prev_reg);
        
        // Stagnation evaluation based on semantic spatial bounds (HDC)
        is_oscillating = (hamming_dist_osc < DRIFT_THRESHOLD);
        is_diminishing = (current_score_reg <= convergence_threshold) && (hamming_dist_prev < (DRIFT_THRESHOLD + 10));
    end

    // ==========================================
    // PIPELINE STAGE 3: Convergence Automata
    // ==========================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cmd_converged      <= 1'b0;
            cmd_abort          <= 1'b0;
            cmd_rotate_persona <= 3'd0;
            c5_hardware_lock   <= 1'b0;
        end else if (eval_enable_reg) begin
            if (current_score_reg > convergence_threshold) begin
                // Path clear - Network Convergence achieved
                cmd_converged      <= 1'b1;
                cmd_rotate_persona <= 3'd0;
            end else if (is_oscillating) begin
                // Hard-lock into Contrarian Persona (2) to break semantic orbit
                cmd_converged      <= 1'b0;
                cmd_rotate_persona <= 3'd2; 
            end else if (is_diminishing) begin
                // Diminishing semantic coverage -> Simplifier Persona (1) or Hacker (3)
                cmd_converged      <= 1'b0;
                cmd_rotate_persona <= 3'd1; 
            end else begin
                // Default un-converged state
                cmd_converged      <= 1'b0;
                cmd_rotate_persona <= 3'd0;
            end
            
            // Output marked as truth (C5-REAL verification lock)
            c5_hardware_lock <= 1'b1; 
        end else begin
            // Reset lock if not evaluating
            c5_hardware_lock <= 1'b0;
        end
    end

endmodule
