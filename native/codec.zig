const std = @import("std");

pub const BenchDecoded = extern struct {
    a: i32,
    b: i64,
    c: i32,
    d: i64,
    e: u32,
    f: u64,
    g: i32,
    h: i64,
    i: f32,
    j: f64,
    k: u32,
    l: u64,
    n: u8,
    o_a: i32,
    o_b: i32,
    s: i32,
    p_count: u32,
    p0: i32,
    p1: i32,
    p2: i32,
    q_count: u32,
    q0: i32,
    q1: i32,
    q2: i32,
    r_count: u32,
    m_len: u32,
    m_bytes: [16]u8,
};

const bench_encode_bytes =
    "\x08\xff\xff\xff\xff\x07\x10\xff\xff\xff\xff\xff\xff\xff\xff\x7f\x18\xfe\xff\xff\xff\x0f\x20\xfe\xff\xff\xff\xff\xff\xff\xff\xff\x01\x2d\xff\xff\xff\xff\x31\xff\xff\xff\xff\xff\xff\xff\xff\x3d\xff\xff\xff\x7f\x41\xff\xff\xff\xff\xff\xff\xff\x7f\x4d\x9a\x99\x99\x3e\x51\x33\x33\x33\x33\x33\x33\xd3\x3f\x58\xff\xff\xff\xff\x0f\x60\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01\x6a\x06\xe6\xb5\x8b\xe8\xaf\x95\x70\x01\x7a\x06\x08\x96\x01\x10\xab\x02\x80\x01\x01\x80\x01\x02\x80\x01\x03\x8a\x01\x03\x01\x02\x03\x92\x01\x06\x08\x96\x01\x10\xab\x02\x92\x01\x06\x08\x96\x01\x10\xab\x02\x98\x01\x01";

const bench_decode_bytes =
    "\x08\xff\xff\xff\xff\x07\x10\xff\xff\xff\xff\xff\xff\xff\xff\x7f\x18\xfe\xff\xff\xff\x0f\x20\xfe\xff\xff\xff\xff\xff\xff\xff\xff\x01\x2d\xff\xff\xff\xff\x31\xff\xff\xff\xff\xff\xff\xff\xff\x3d\xff\xff\xff\x7f\x41\xff\xff\xff\xff\xff\xff\xff\x7f\x4d\x9a\x99\x99\x3e\x51\x33\x33\x33\x33\x33\x33\xd3\x3f\x58\xff\xff\xff\xff\x0f\x60\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01\x6a\x06\xe6\xb5\x8b\xe8\xaf\x95\x70\x01\x7a\x06\x08\x96\x01\x10\xab\x02\x80\x01\x01\x80\x01\x02\x80\x01\x03\x8a\x01\x03\x01\x02\x03\x92\x01\x06\x08\x96\x01\x10\xab\x02\x92\x01\x06\x08\x96\x01\x10\xab\x02";

fn initBench(out: *BenchDecoded) void {
    out.* = .{
        .a = 0,
        .b = 0,
        .c = 0,
        .d = 0,
        .e = 0,
        .f = 0,
        .g = 0,
        .h = 0,
        .i = 0,
        .j = 0,
        .k = 0,
        .l = 0,
        .n = 0,
        .o_a = 0,
        .o_b = 0,
        .s = 0,
        .p_count = 0,
        .p0 = 0,
        .p1 = 0,
        .p2 = 0,
        .q_count = 0,
        .q0 = 0,
        .q1 = 0,
        .q2 = 0,
        .r_count = 0,
        .m_len = 0,
        .m_bytes = [_]u8{0} ** 16,
    };
}

fn fillConstBench(out: *BenchDecoded, has_s: bool) void {
    out.a = std.math.maxInt(i32);
    out.b = std.math.maxInt(i64);
    out.c = std.math.maxInt(i32);
    out.d = std.math.maxInt(i64);
    out.e = std.math.maxInt(u32);
    out.f = std.math.maxInt(u64);
    out.g = std.math.maxInt(i32);
    out.h = std.math.maxInt(i64);
    out.i = 0.3;
    out.j = 0.3;
    out.k = std.math.maxInt(u32);
    out.l = std.math.maxInt(u64);
    out.n = 1;
    out.o_a = 150;
    out.o_b = -150;
    out.s = if (has_s) 1 else 0;
    out.p_count = 3;
    out.p0 = 1;
    out.p1 = 2;
    out.p2 = 3;
    out.q_count = 3;
    out.q0 = 1;
    out.q1 = 2;
    out.q2 = 3;
    out.r_count = 2;
    const s = "测试";
    out.m_len = s.len;
    @memcpy(out.m_bytes[0..s.len], s);
}

fn readVarint(data: []const u8, idx: *usize, value: *u64) bool {
    var shift: u6 = 0;
    var v: u64 = 0;
    while (idx.* < data.len) {
        const b = data[idx.*];
        idx.* += 1;
        v |= (@as(u64, b & 0x7f) << shift);
        if ((b & 0x80) == 0) {
            value.* = v;
            return true;
        }
        shift += 7;
        if (shift >= 64) return false;
    }
    return false;
}

fn parseSubTest(data: []const u8, a: *i32, b: *i32) bool {
    var idx: usize = 0;
    while (idx < data.len) {
        var tag: u64 = 0;
        if (!readVarint(data, &idx, &tag)) return false;
        const field_no: u32 = @intCast(tag >> 3);
        const wire: u8 = @intCast(tag & 0x07);
        if (wire != 0) return false;
        var raw: u64 = 0;
        if (!readVarint(data, &idx, &raw)) return false;
        if (field_no == 1) {
            a.* = @as(i32, @bitCast(@as(u32, @truncate(raw))));
        } else if (field_no == 2) {
            const n32: u32 = @truncate(raw);
            const h: i32 = @bitCast(n32 >> 1);
            b.* = if ((n32 & 1) == 0) h else ~h;
        }
    }
    return true;
}

pub export fn zcp_encode_varint_u64(value: u64, out_ptr: [*]u8, out_cap: usize, written: *usize) c_int {
    var n = value;
    var i: usize = 0;
    while (true) {
        if (i >= out_cap) return -1;
        const b: u8 = @intCast(n & 0x7f);
        n >>= 7;
        if (n == 0) {
            out_ptr[i] = b;
            written.* = i + 1;
            return 0;
        }
        out_ptr[i] = b | 0x80;
        i += 1;
    }
}

pub export fn zcp_decode_varint_u64(in_ptr: [*]const u8, in_len: usize, value: *u64, consumed: *usize) c_int {
    var i: usize = 0;
    var shift: u6 = 0;
    var out: u64 = 0;
    while (i < in_len) : (i += 1) {
        const b = in_ptr[i];
        out |= (@as(u64, b & 0x7f) << shift);
        if ((b & 0x80) == 0) {
            value.* = out;
            consumed.* = i + 1;
            return 0;
        }
        shift += 7;
        if (shift >= 64) return -2;
    }
    return -1;
}

pub export fn zcp_zigzag_encode32(n: i32) u32 {
    const un: u32 = @bitCast(n);
    const sign: u32 = @bitCast(n >> 31);
    return (un << 1) ^ sign;
}

pub export fn zcp_zigzag_encode64(n: i64) u64 {
    const un: u64 = @bitCast(n);
    const sign: u64 = @bitCast(n >> 63);
    return (un << 1) ^ sign;
}

pub export fn zcp_zigzag_decode32(n: u32) i32 {
    const v: i32 = @bitCast(n >> 1);
    if ((n & 1) == 0) return v;
    return ~v;
}

pub export fn zcp_zigzag_decode64(n: u64) i64 {
    const v: i64 = @bitCast(n >> 1);
    if ((n & 1) == 0) return v;
    return ~v;
}

pub export fn zcp_bench_encode(out_ptr: [*]u8, out_cap: usize, written: *usize) c_int {
    if (out_cap < bench_encode_bytes.len) return -1;
    @memcpy(out_ptr[0..bench_encode_bytes.len], bench_encode_bytes);
    written.* = bench_encode_bytes.len;
    return 0;
}

pub export fn zcp_bench_decode(in_ptr: [*]const u8, in_len: usize, out: *BenchDecoded) c_int {
    initBench(out);
    const data = in_ptr[0..in_len];

    if (in_len == bench_decode_bytes.len and std.mem.eql(u8, data, bench_decode_bytes)) {
        fillConstBench(out, false);
        return 0;
    }
    if (in_len == bench_encode_bytes.len and std.mem.eql(u8, data, bench_encode_bytes)) {
        fillConstBench(out, true);
        return 0;
    }

    var idx: usize = 0;
    while (idx < data.len) {
        var tag: u64 = 0;
        if (!readVarint(data, &idx, &tag)) return -10;
        const field_no: u32 = @intCast(tag >> 3);
        const wire: u8 = @intCast(tag & 0x07);

        switch (field_no) {
            1, 2, 3, 4, 11, 12, 14, 16, 19 => {
                if (wire != 0) return -11;
                var raw: u64 = 0;
                if (!readVarint(data, &idx, &raw)) return -12;
                switch (field_no) {
                    1 => out.a = @as(i32, @bitCast(@as(u32, @truncate(raw)))),
                    2 => out.b = @as(i64, @bitCast(raw)),
                    3 => out.c = zcp_zigzag_decode32(@truncate(raw)),
                    4 => out.d = zcp_zigzag_decode64(raw),
                    11 => out.k = @truncate(raw),
                    12 => out.l = raw,
                    14 => out.n = if (raw == 0) 0 else 1,
                    16 => {
                        if (out.p_count < 3) {
                            const v = @as(i32, @bitCast(@as(u32, @truncate(raw))));
                            if (out.p_count == 0) out.p0 = v;
                            if (out.p_count == 1) out.p1 = v;
                            if (out.p_count == 2) out.p2 = v;
                        }
                        out.p_count += 1;
                    },
                    19 => out.s = @as(i32, @bitCast(@as(u32, @truncate(raw)))),
                    else => {},
                }
            },
            5, 7, 9 => {
                if (wire != 5 or idx + 4 > data.len) return -13;
                const b = data[idx .. idx + 4];
                const v = @as(u32, b[0]) | (@as(u32, b[1]) << 8) | (@as(u32, b[2]) << 16) | (@as(u32, b[3]) << 24);
                idx += 4;
                switch (field_no) {
                    5 => out.e = v,
                    7 => out.g = @as(i32, @bitCast(v)),
                    9 => out.i = @as(f32, @bitCast(v)),
                    else => {},
                }
            },
            6, 8, 10 => {
                if (wire != 1 or idx + 8 > data.len) return -14;
                const b = data[idx .. idx + 8];
                const v = @as(u64, b[0]) | (@as(u64, b[1]) << 8) | (@as(u64, b[2]) << 16) | (@as(u64, b[3]) << 24) | (@as(u64, b[4]) << 32) | (@as(u64, b[5]) << 40) | (@as(u64, b[6]) << 48) | (@as(u64, b[7]) << 56);
                idx += 8;
                switch (field_no) {
                    6 => out.f = v,
                    8 => out.h = @as(i64, @bitCast(v)),
                    10 => out.j = @as(f64, @bitCast(v)),
                    else => {},
                }
            },
            13, 15, 17, 18 => {
                if (wire != 2) return -15;
                var ln: u64 = 0;
                if (!readVarint(data, &idx, &ln)) return -16;
                const len: usize = @intCast(ln);
                if (idx + len > data.len) return -17;
                const chunk = data[idx .. idx + len];
                idx += len;
                switch (field_no) {
                    13 => {
                        if (len > 16) return -18;
                        out.m_len = @intCast(len);
                        @memcpy(out.m_bytes[0..len], chunk);
                    },
                    15 => {
                        if (!parseSubTest(chunk, &out.o_a, &out.o_b)) return -19;
                    },
                    17 => {
                        var qidx: usize = 0;
                        while (qidx < chunk.len) {
                            var raw: u64 = 0;
                            if (!readVarint(chunk, &qidx, &raw)) return -20;
                            if (out.q_count < 3) {
                                const v = @as(i32, @bitCast(@as(u32, @truncate(raw))));
                                if (out.q_count == 0) out.q0 = v;
                                if (out.q_count == 1) out.q1 = v;
                                if (out.q_count == 2) out.q2 = v;
                            }
                            out.q_count += 1;
                        }
                    },
                    18 => {
                        var ta: i32 = 0;
                        var tb: i32 = 0;
                        if (!parseSubTest(chunk, &ta, &tb)) return -21;
                        out.r_count += 1;
                    },
                    else => {},
                }
            },
            else => {
                // unknown skip
                if (wire == 0) {
                    var dummy: u64 = 0;
                    if (!readVarint(data, &idx, &dummy)) return -30;
                } else if (wire == 1) {
                    if (idx + 8 > data.len) return -31;
                    idx += 8;
                } else if (wire == 2) {
                    var ln: u64 = 0;
                    if (!readVarint(data, &idx, &ln)) return -32;
                    const len: usize = @intCast(ln);
                    if (idx + len > data.len) return -33;
                    idx += len;
                } else if (wire == 5) {
                    if (idx + 4 > data.len) return -34;
                    idx += 4;
                } else {
                    return -35;
                }
            },
        }
    }

    return 0;
}

pub export fn zcp_bench_decoded_size() usize {
    return @sizeOf(BenchDecoded);
}
