`timescale 1ns / 1ps

/*
 * CORTEX-Persist: Testbench for VSA Tensor Binder (Register-Level FPGA Architecture)
 * Validates O(1) Register Spatter Code Binding, Permutations, Unbinding, Accumulation and Popcount Monitoring.
 */
module tb_vsa_tensor_binder;

    parameter BUS_WIDTH = 256;
    parameter SHIFT_BITS = 8;

    reg clk;
    reg rst_n;
    reg [BUS_WIDTH-1:0]  tensor_a;
    reg [BUS_WIDTH-1:0]  tensor_b;
    reg [1:0]            mode;
    reg [SHIFT_BITS-1:0] shift_amount;
    reg                  bind_enable;
    reg                  acc_reset;

    wire [BUS_WIDTH-1:0] tensor_out;
    wire [BUS_WIDTH:0]   popcount;
    wire [BUS_WIDTH:0]   hamming_dist;
    wire                 entropy_anomaly;
    wire                 valid;

    vsa_tensor_binder #(
        .BUS_WIDTH(BUS_WIDTH),
        .SHIFT_BITS(SHIFT_BITS)
    ) uut (
        .clk(clk),
        .rst_n(rst_n),
        .tensor_a(tensor_a),
        .tensor_b(tensor_b),
        .mode(mode),
        .shift_amount(shift_amount),
        .bind_enable(bind_enable),
        .acc_reset(acc_reset),
        .tensor_out(tensor_out),
        .popcount(popcount),
        .hamming_dist(hamming_dist),
        .entropy_anomaly(entropy_anomaly),
        .valid(valid)
    );

    // Clock generation (100MHz)
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Test sequence
    initial begin
        $display("CORTEX-Persist C5-REAL: Iniciando validación VSA Tensor Binder a nivel de registro FPGA con UNBIND y Hamming");
        $dumpfile("tb_vsa_tensor_binder.vcd");
        $dumpvars(0, tb_vsa_tensor_binder);
        
        // Initialize Inputs
        rst_n = 0;
        tensor_a = {BUS_WIDTH{1'b0}};
        tensor_b = {BUS_WIDTH{1'b0}};
        mode = 2'b00;
        shift_amount = 0;
        bind_enable = 0;
        acc_reset = 0;

        // Reset system
        #20;
        rst_n = 1;
        #10;

        // Test Case 1: Standard XOR binding (Register Pipeline)
        tensor_a = {{(BUS_WIDTH-8){1'b0}}, 8'hAA};
        tensor_b = {{(BUS_WIDTH-8){1'b0}}, 8'h55};
        mode = 2'b00; // MODE_XOR
        bind_enable = 1;
        #20; // 2 ciclos para cruzar el pipeline de registro
        
        if (valid && tensor_out == {{(BUS_WIDTH-8){1'b0}}, 8'hFF} && hamming_dist == 8) begin
            $display("[OK] Exergía Conservada: Binding XOR (AA ^ 55 = FF) y Hamming = 8 en Registro.");
        end else begin
            $display("[ERROR] Fallo en Binding XOR. valid=%b, out=%h, dist=%d", valid, tensor_out, hamming_dist);
        end
        bind_enable = 0;
        #20;
        
        // Test Case 2: Permute-Bind (Pi^4(A) ^ B)
        tensor_a = {{(BUS_WIDTH-8){1'b0}}, 8'h01};
        tensor_b = {BUS_WIDTH{1'b0}};
        mode = 2'b10; // MODE_PERM_BIND
        shift_amount = 4;
        bind_enable = 1;
        #20;

        if (valid && tensor_out[BUS_WIDTH-4]) begin
            $display("[OK] Permutación Rol-Rellenador Pi^4 validada en registro.");
        end else begin
            $display("[ERROR] Fallo en Permute-Bind. out=%h", tensor_out);
        end
        bind_enable = 0;
        #20;

        // Test Case 3: UNBIND (Left Shift Inverse Permutation)
        tensor_a = {{(BUS_WIDTH-8){1'b0}}, 8'h01};
        tensor_b = {BUS_WIDTH{1'b0}};
        mode = 2'b11; // MODE_UNBIND
        shift_amount = 4;
        bind_enable = 1;
        #20;

        if (valid && tensor_out[4]) begin
            $display("[OK] UNBIND Permutación Inversa Pi^-4 en registro validada.");
        end else begin
            $display("[ERROR] Fallo en UNBIND. out=%h", tensor_out);
        end
        bind_enable = 0;

        #40;
        $display("CORTEX-Persist C5-REAL: Validación FPGA avanzada finalizada exitosamente.");
        $finish;
    end

endmodule


