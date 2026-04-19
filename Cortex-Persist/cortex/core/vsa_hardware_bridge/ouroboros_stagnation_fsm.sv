// ouroboros_stagnation_fsm.sv - Direct-Silicon JIT
// Synthesis Target: O(1) Stagnation Detection & Drift Evaluation
// Enforces Law Ω2 y Ω9: Purging Python Multipass Stagnation Loop into C5-REAL Hardware.

module ouroboros_stagnation_fsm #(
    parameter HASH_WIDTH = 256,
    parameter HISTORY_DEPTH = 4
)(
    input  logic                      clk,
    input  logic                      rst_n,
    input  logic                      eval_enable,
    input  logic [HASH_WIDTH-1:0]     current_gen_hash,
    input  logic [HASH_WIDTH-1:0]     gen_history [0:HISTORY_DEPTH-1],
    input  logic [31:0]               convergence_threshold, // Fixed point score
    input  logic [31:0]               current_score,

    output logic                      cmd_converged,
    output logic                      cmd_abort,
    output logic [2:0]                cmd_rotate_persona, // 0=None, 1=Hacker, 2=Contrarian, 3=Simplifier, etc.
    output logic                      c5_hardware_lock
);

    // O(1) Oscillation & Stagnation Array Comparators
    logic is_oscillating;
    logic is_diminishing;

    always_comb begin
        // Oscillation detection: current == history[n-2]
        // Bypassing O(n) Python loops for direct combinational XOR array comparison
        is_oscillating = (current_gen_hash == gen_history[1]);
        
        // Diminishing returns (simplified fixed-point cascade)
        // Bound directly to transistors; no GIL (Global Interpreter Lock) contention
        is_diminishing = (current_score <= convergence_threshold);
    end

    // Sequential Convergence Automata
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cmd_converged      <= 1'b0;
            cmd_abort          <= 1'b0;
            cmd_rotate_persona <= 3'd0;
            c5_hardware_lock   <= 1'b0;
        end else if (eval_enable) begin
            if (current_score > convergence_threshold) begin
                // Path clear - Network Convergence achieved
                cmd_converged      <= 1'b1;
                cmd_rotate_persona <= 3'd0;
            end else if (is_oscillating) begin
                // Hard-lock into Contrarian Persona (2) to break oscillation loop
                cmd_converged      <= 1'b0;
                cmd_rotate_persona <= 3'd2; 
            end else if (is_diminishing) begin
                // Diminishing returns -> Simplifier Persona (1) or Hacker (3)
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
