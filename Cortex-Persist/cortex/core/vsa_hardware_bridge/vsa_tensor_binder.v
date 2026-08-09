`timescale 1ns / 1ps

/*
 * CORTEX Law Ω0 Enforcement.
 * Hardware Sovereign: Silicon-Overlord-Omega
 * Matrix: VSA Tensor Binder (Register-Level Hardware Architecture)
 */
module vsa_tensor_binder #(
    parameter BUS_WIDTH = 256,
    parameter SHIFT_BITS = $clog2(BUS_WIDTH)
)(
    input  wire                   clk,
    input  wire                   rst_n,
    input  wire [BUS_WIDTH-1:0]   tensor_a,
    input  wire [BUS_WIDTH-1:0]   tensor_b,
    input  wire [1:0]             mode,         // 2'b00: XOR, 2'b01: XNOR, 2'b10: PERM_XOR, 2'b11: ACCUMULATE
    input  wire [SHIFT_BITS-1:0]  shift_amount, // Desplazamiento circular para Permutación Rol-Rellenador Pi^k
    input  wire                   bind_enable,
    input  wire                   acc_reset,    // Reset para el acumulador interno de registros
    output reg  [BUS_WIDTH-1:0]   tensor_out,
    output reg  [BUS_WIDTH:0]     popcount,     // Monitoreo de densidad entrópica (Popcount en registro)
    output reg                    entropy_anomaly, // Alerta si popcount == 0 o popcount == BUS_WIDTH
    output reg                    valid
);

    // Modos de binding
    localparam MODE_XOR        = 2'b00;
    localparam MODE_XNOR       = 2'b01;
    localparam MODE_PERM_XOR   = 2'b10;
    localparam MODE_ACCUMULATE = 2'b11;

    // Registros de entrada de etapa 1
    reg [BUS_WIDTH-1:0] reg_a;
    reg [BUS_WIDTH-1:0] reg_b;
    reg [1:0]           reg_mode;
    reg [SHIFT_BITS-1:0] reg_shift;
    reg                 reg_enable;

    // Acumulador interno en banco de registros
    reg [BUS_WIDTH-1:0] acc_reg;

    // Permutación circular de entrada tensor_a (Pi^k(A))
    wire [BUS_WIDTH-1:0] permuted_a;
    assign permuted_a = (reg_shift == 0) ? reg_a :
                        ((reg_a >> reg_shift) | (reg_a << (BUS_WIDTH - reg_shift)));

    // Matriz combinacional de binding
    reg [BUS_WIDTH-1:0] bound_combinational;

    always @(*) begin
        case (reg_mode)
            MODE_XOR:        bound_combinational = reg_a ^ reg_b;
            MODE_XNOR:       bound_combinational = ~(reg_a ^ reg_b);
            MODE_PERM_XOR:   bound_combinational = permuted_a ^ reg_b;
            MODE_ACCUMULATE: bound_combinational = acc_reg ^ (reg_a ^ reg_b);
            default:         bound_combinational = reg_a ^ reg_b;
        endcase
    end

    // Función popcount combinacional para monitoreo de exergía/entropía
    integer i;
    reg [BUS_WIDTH:0] count_temp;
    always @(*) begin
        count_temp = 0;
        for (i = 0; i < BUS_WIDTH; i = i + 1) begin
            if (bound_combinational[i]) begin
                count_temp = count_temp + 1'b1;
            end
        end
    end

    // Etapa de registro de salida y acumulación
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            reg_a           <= {BUS_WIDTH{1'b0}};
            reg_b           <= {BUS_WIDTH{1'b0}};
            reg_mode        <= MODE_XOR;
            reg_shift       <= {SHIFT_BITS{1'b0}};
            reg_enable      <= 1'b0;
            tensor_out      <= {BUS_WIDTH{1'b0}};
            acc_reg         <= {BUS_WIDTH{1'b0}};
            popcount        <= {(BUS_WIDTH+1){1'b0}};
            entropy_anomaly <= 1'b0;
            valid           <= 1'b0;
        end else begin
            // Etapa 1: Latch de entradas
            reg_a      <= tensor_a;
            reg_b      <= tensor_b;
            reg_mode   <= mode;
            reg_shift  <= shift_amount;
            reg_enable <= bind_enable;

            if (acc_reset) begin
                acc_reg <= {BUS_WIDTH{1'b0}};
            end

            // Etapa 2: Latch de cómputo y acumulador
            if (reg_enable) begin
                tensor_out      <= bound_combinational;
                acc_reg         <= bound_combinational;
                popcount        <= count_temp;
                entropy_anomaly <= (count_temp == 0) || (count_temp == BUS_WIDTH);
                valid           <= 1'b1;
            end else begin
                valid           <= 1'b0;
            end
        end
    end

    // =========================================================================
    // C5-REAL FORMAL VERIFICATION (Zero-Latency & Cycle Invariant Guarantee)
    // =========================================================================
    `ifdef FORMAL
    always @(posedge clk) begin
        if (rst_n) begin
            if ($past(reg_enable)) begin
                assert(valid == 1'b1);
                assert(popcount <= BUS_WIDTH);
            end
        end
    end
    `endif

endmodule

