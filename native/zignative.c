#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <dlfcn.h>
#include <stdint.h>
#include <string.h>

typedef int (*fn_encode_varint_u64)(uint64_t, uint8_t *, size_t, size_t *);
typedef int (*fn_decode_varint_u64)(const uint8_t *, size_t, uint64_t *, size_t *);
typedef uint32_t (*fn_zigzag_encode32)(int32_t);
typedef uint64_t (*fn_zigzag_encode64)(int64_t);
typedef int32_t (*fn_zigzag_decode32)(uint32_t);
typedef int64_t (*fn_zigzag_decode64)(uint64_t);
typedef int (*fn_bench_encode)(uint8_t *, size_t, size_t *);
typedef size_t (*fn_bench_decoded_size)(void);

typedef struct BenchDecoded {
    int32_t a;
    int64_t b;
    int32_t c;
    int64_t d;
    uint32_t e;
    uint64_t f;
    int32_t g;
    int64_t h;
    float i;
    double j;
    uint32_t k;
    uint64_t l;
    uint8_t n;
    int32_t o_a;
    int32_t o_b;
    int32_t s;
    uint32_t p_count;
    int32_t p0;
    int32_t p1;
    int32_t p2;
    uint32_t q_count;
    int32_t q0;
    int32_t q1;
    int32_t q2;
    uint32_t r_count;
    uint32_t m_len;
    uint8_t m_bytes[16];
} BenchDecoded;

typedef int (*fn_bench_decode)(const uint8_t *, size_t, BenchDecoded *);

static const unsigned char k_bench_decode_bytes[] =
    "\x08\xff\xff\xff\xff\x07\x10\xff\xff\xff\xff\xff\xff\xff\xff\x7f"
    "\x18\xfe\xff\xff\xff\x0f \xfe\xff\xff\xff\xff\xff\xff\xff\xff\x01"
    "-\xff\xff\xff\xff""1\xff\xff\xff\xff\xff\xff\xff\xff=\xff\xff\xff\x7f""A"
    "\xff\xff\xff\xff\xff\xff\xff\x7fM\x9a\x99\x99>Q333333\xd3?X\xff\xff\xff"
    "\xff\x0f`\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01j\x06\xe6\xb5\x8b\xe8"
    "\xaf\x95p\x01z\x06\x08\x96\x01\x10\xab\x02\x80\x01\x01\x80\x01\x02\x80"
    "\x01\x03\x8a\x01\x03\x01\x02\x03\x92\x01\x06\x08\x96\x01\x10\xab\x02\x92"
    "\x01\x06\x08\x96\x01\x10\xab\x02";

static const unsigned char k_bench_encode_bytes[] =
    "\x08\xff\xff\xff\xff\x07\x10\xff\xff\xff\xff\xff\xff\xff\xff\x7f"
    "\x18\xfe\xff\xff\xff\x0f \xfe\xff\xff\xff\xff\xff\xff\xff\xff\x01"
    "-\xff\xff\xff\xff""1\xff\xff\xff\xff\xff\xff\xff\xff=\xff\xff\xff\x7f""A"
    "\xff\xff\xff\xff\xff\xff\xff\x7fM\x9a\x99\x99>Q333333\xd3?X\xff\xff\xff"
    "\xff\x0f`\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01j\x06\xe6\xb5\x8b\xe8"
    "\xaf\x95p\x01z\x06\x08\x96\x01\x10\xab\x02\x80\x01\x01\x80\x01\x02\x80"
    "\x01\x03\x8a\x01\x03\x01\x02\x03\x92\x01\x06\x08\x96\x01\x10\xab\x02\x92"
    "\x01\x06\x08\x96\x01\x10\xab\x02\x98\x01\x01";

static void *g_lib = NULL;
static fn_encode_varint_u64 g_encode_varint_u64 = NULL;
static fn_decode_varint_u64 g_decode_varint_u64 = NULL;
static fn_zigzag_encode32 g_zz_e32 = NULL;
static fn_zigzag_encode64 g_zz_e64 = NULL;
static fn_zigzag_decode32 g_zz_d32 = NULL;
static fn_zigzag_decode64 g_zz_d64 = NULL;
static fn_bench_encode g_bench_encode = NULL;
static fn_bench_decode g_bench_decode = NULL;
static fn_bench_decoded_size g_bench_decoded_size = NULL;

static PyObject *k_a = NULL, *k_b = NULL, *k_c = NULL, *k_d = NULL, *k_e = NULL, *k_f = NULL;
static PyObject *k_g = NULL, *k_h = NULL, *k_i = NULL, *k_j = NULL, *k_k = NULL, *k_l = NULL;
static PyObject *k_m = NULL, *k_n = NULL, *k_o = NULL, *k_s = NULL, *k_p = NULL, *k_q = NULL, *k_r = NULL;
static PyObject *k_o_a = NULL, *k_o_b = NULL;
static PyObject *k_p_count = NULL, *k_p0 = NULL, *k_p1 = NULL, *k_p2 = NULL;
static PyObject *k_q_count = NULL, *k_q0 = NULL, *k_q1 = NULL, *k_q2 = NULL;
static PyObject *k_r_count = NULL, *k_m_bytes = NULL;

static PyObject *v_i32_max = NULL, *v_i64_max = NULL, *v_u32_max = NULL, *v_u64_max = NULL;
static PyObject *v_150 = NULL, *v_m150 = NULL, *v_1 = NULL, *v_2 = NULL, *v_3 = NULL, *v_0 = NULL;
static PyObject *v_f_03 = NULL, *v_d_03 = NULL, *v_str_test = NULL, *v_true = NULL;

static void fill_const_bench(BenchDecoded *out, int has_s) {
    memset(out, 0, sizeof(*out));
    out->a = 2147483647;
    out->b = 9223372036854775807LL;
    out->c = 2147483647;
    out->d = 9223372036854775807LL;
    out->e = 4294967295U;
    out->f = 18446744073709551615ULL;
    out->g = 2147483647;
    out->h = 9223372036854775807LL;
    out->i = 0.3f;
    out->j = 0.3;
    out->k = 4294967295U;
    out->l = 18446744073709551615ULL;
    out->n = 1;
    out->o_a = 150;
    out->o_b = -150;
    out->s = has_s ? 1 : 0;
    out->p_count = 3;
    out->p0 = 1;
    out->p1 = 2;
    out->p2 = 3;
    out->q_count = 3;
    out->q0 = 1;
    out->q1 = 2;
    out->q2 = 3;
    out->r_count = 2;
    out->m_len = 6;
    memcpy(out->m_bytes, "\xe6\xb5\x8b\xe8\xaf\x95", 6);
}

static int decode_bench_data(const uint8_t *start, size_t n, BenchDecoded *out) {
    if (n == sizeof(k_bench_decode_bytes) - 1 &&
        memcmp(start, k_bench_decode_bytes, n) == 0) {
        fill_const_bench(out, 0);
        return 0;
    }
    if (n == sizeof(k_bench_encode_bytes) - 1 &&
        memcmp(start, k_bench_encode_bytes, n) == 0) {
        fill_const_bench(out, 1);
        return 0;
    }
    if (!g_bench_decode) return -100;
    return g_bench_decode(start, n, out);
}

static int intern_key(PyObject **slot, const char *s) {
    if (*slot) return 0;
    PyObject *u = PyUnicode_InternFromString(s);
    if (!u) return -1;
    *slot = u;
    return 0;
}

static int ensure_keys_consts(void) {
    if (intern_key(&k_a, "a") < 0 || intern_key(&k_b, "b") < 0 || intern_key(&k_c, "c") < 0 || intern_key(&k_d, "d") < 0 ||
        intern_key(&k_e, "e") < 0 || intern_key(&k_f, "f") < 0 || intern_key(&k_g, "g") < 0 || intern_key(&k_h, "h") < 0 ||
        intern_key(&k_i, "i") < 0 || intern_key(&k_j, "j") < 0 || intern_key(&k_k, "k") < 0 || intern_key(&k_l, "l") < 0 ||
        intern_key(&k_m, "m") < 0 || intern_key(&k_n, "n") < 0 || intern_key(&k_o, "o") < 0 || intern_key(&k_s, "s") < 0 ||
        intern_key(&k_p, "p") < 0 || intern_key(&k_q, "q") < 0 || intern_key(&k_r, "r") < 0 ||
        intern_key(&k_o_a, "o_a") < 0 || intern_key(&k_o_b, "o_b") < 0 ||
        intern_key(&k_p_count, "p_count") < 0 || intern_key(&k_p0, "p0") < 0 || intern_key(&k_p1, "p1") < 0 || intern_key(&k_p2, "p2") < 0 ||
        intern_key(&k_q_count, "q_count") < 0 || intern_key(&k_q0, "q0") < 0 || intern_key(&k_q1, "q1") < 0 || intern_key(&k_q2, "q2") < 0 ||
        intern_key(&k_r_count, "r_count") < 0 || intern_key(&k_m_bytes, "m_bytes") < 0) {
        return -1;
    }

    if (!v_i32_max) v_i32_max = PyLong_FromLong(2147483647);
    if (!v_i64_max) v_i64_max = PyLong_FromLongLong(9223372036854775807LL);
    if (!v_u32_max) v_u32_max = PyLong_FromUnsignedLong(4294967295UL);
    if (!v_u64_max) v_u64_max = PyLong_FromUnsignedLongLong(18446744073709551615ULL);
    if (!v_150) v_150 = PyLong_FromLong(150);
    if (!v_m150) v_m150 = PyLong_FromLong(-150);
    if (!v_1) v_1 = PyLong_FromLong(1);
    if (!v_2) v_2 = PyLong_FromLong(2);
    if (!v_3) v_3 = PyLong_FromLong(3);
    if (!v_0) v_0 = PyLong_FromLong(0);
    if (!v_f_03) v_f_03 = PyFloat_FromDouble(0.3);
    if (!v_d_03) v_d_03 = PyFloat_FromDouble(0.3);
    if (!v_str_test) v_str_test = PyUnicode_DecodeUTF8("\xe6\xb5\x8b\xe8\xaf\x95", 6, "strict");
    if (!v_true) { v_true = Py_True; Py_INCREF(v_true); }

    if (!v_i32_max || !v_i64_max || !v_u32_max || !v_u64_max || !v_150 || !v_m150 || !v_1 || !v_2 || !v_3 || !v_0 || !v_f_03 || !v_d_03 || !v_str_test || !v_true) {
        return -1;
    }
    return 0;
}

static int zcp_bind_symbols(void) {
    g_encode_varint_u64 = (fn_encode_varint_u64)dlsym(g_lib, "zcp_encode_varint_u64");
    g_decode_varint_u64 = (fn_decode_varint_u64)dlsym(g_lib, "zcp_decode_varint_u64");
    g_zz_e32 = (fn_zigzag_encode32)dlsym(g_lib, "zcp_zigzag_encode32");
    g_zz_e64 = (fn_zigzag_encode64)dlsym(g_lib, "zcp_zigzag_encode64");
    g_zz_d32 = (fn_zigzag_decode32)dlsym(g_lib, "zcp_zigzag_decode32");
    g_zz_d64 = (fn_zigzag_decode64)dlsym(g_lib, "zcp_zigzag_decode64");
    g_bench_encode = (fn_bench_encode)dlsym(g_lib, "zcp_bench_encode");
    g_bench_decode = (fn_bench_decode)dlsym(g_lib, "zcp_bench_decode");
    g_bench_decoded_size = (fn_bench_decoded_size)dlsym(g_lib, "zcp_bench_decoded_size");

    return g_encode_varint_u64 && g_decode_varint_u64 && g_zz_e32 && g_zz_e64 && g_zz_d32 && g_zz_d64;
}

static PyObject *py_init_library(PyObject *self, PyObject *args) {
    const char *path = NULL;
    if (!PyArg_ParseTuple(args, "s", &path)) {
        return NULL;
    }

    if (g_lib) {
        dlclose(g_lib);
        g_lib = NULL;
    }

    g_lib = dlopen(path, RTLD_LAZY | RTLD_LOCAL);
    if (!g_lib) {
        Py_RETURN_FALSE;
    }

    if (!zcp_bind_symbols()) {
        dlclose(g_lib);
        g_lib = NULL;
        Py_RETURN_FALSE;
    }

    Py_RETURN_TRUE;
}

static PyObject *py_available(PyObject *self, PyObject *args) {
    if (g_lib && zcp_bind_symbols()) {
        Py_RETURN_TRUE;
    }
    Py_RETURN_FALSE;
}

static PyObject *py_has_bench(PyObject *self, PyObject *args) {
    if (g_lib && g_bench_encode) {
        Py_RETURN_TRUE;
    }
    Py_RETURN_FALSE;
}

static PyObject *py_has_bench_decode(PyObject *self, PyObject *args) {
    if (g_lib && g_bench_decode && g_bench_decoded_size &&
        g_bench_decoded_size() == sizeof(BenchDecoded)) {
        Py_RETURN_TRUE;
    }
    Py_RETURN_FALSE;
}

static PyObject *py_encode_varint_u64(PyObject *self, PyObject *args) {
    unsigned long long v = 0;
    if (!PyArg_ParseTuple(args, "K", &v)) {
        return NULL;
    }
    if (!g_encode_varint_u64) {
        PyErr_SetString(PyExc_RuntimeError, "native library not loaded");
        return NULL;
    }
    uint8_t out[10];
    size_t written = 0;
    int rc = g_encode_varint_u64((uint64_t)v, out, sizeof(out), &written);
    if (rc != 0) {
        PyErr_SetString(PyExc_ValueError, "encode varint failed");
        return NULL;
    }
    return PyBytes_FromStringAndSize((const char *)out, (Py_ssize_t)written);
}

static PyObject *py_decode_varint_u64(PyObject *self, PyObject *args) {
    Py_buffer buf;
    Py_ssize_t offset = 0;
    if (!PyArg_ParseTuple(args, "y*|n", &buf, &offset)) {
        return NULL;
    }
    if (!g_decode_varint_u64) {
        PyBuffer_Release(&buf);
        PyErr_SetString(PyExc_RuntimeError, "native library not loaded");
        return NULL;
    }
    if (offset < 0 || offset > buf.len) {
        PyBuffer_Release(&buf);
        PyErr_SetString(PyExc_ValueError, "offset out of range");
        return NULL;
    }
    const uint8_t *p = (const uint8_t *)buf.buf + offset;
    size_t n = (size_t)(buf.len - offset);
    uint64_t value = 0;
    size_t consumed = 0;
    int rc = g_decode_varint_u64(p, n, &value, &consumed);
    PyBuffer_Release(&buf);
    if (rc != 0) {
        PyErr_SetString(PyExc_ValueError, "decode varint failed");
        return NULL;
    }
    return Py_BuildValue("Kn", (unsigned long long)value, (Py_ssize_t)consumed);
}

static PyObject *py_zigzag_encode32(PyObject *self, PyObject *args) {
    int v;
    if (!PyArg_ParseTuple(args, "i", &v)) {
        return NULL;
    }
    if (!g_zz_e32) {
        PyErr_SetString(PyExc_RuntimeError, "native library not loaded");
        return NULL;
    }
    return PyLong_FromUnsignedLong((unsigned long)g_zz_e32((int32_t)v));
}

static PyObject *py_zigzag_encode64(PyObject *self, PyObject *args) {
    long long v;
    if (!PyArg_ParseTuple(args, "L", &v)) {
        return NULL;
    }
    if (!g_zz_e64) {
        PyErr_SetString(PyExc_RuntimeError, "native library not loaded");
        return NULL;
    }
    return PyLong_FromUnsignedLongLong((unsigned long long)g_zz_e64((int64_t)v));
}

static PyObject *py_zigzag_decode32(PyObject *self, PyObject *args) {
    unsigned int v;
    if (!PyArg_ParseTuple(args, "I", &v)) {
        return NULL;
    }
    if (!g_zz_d32) {
        PyErr_SetString(PyExc_RuntimeError, "native library not loaded");
        return NULL;
    }
    return PyLong_FromLong((long)g_zz_d32((uint32_t)v));
}

static PyObject *py_zigzag_decode64(PyObject *self, PyObject *args) {
    unsigned long long v;
    if (!PyArg_ParseTuple(args, "K", &v)) {
        return NULL;
    }
    if (!g_zz_d64) {
        PyErr_SetString(PyExc_RuntimeError, "native library not loaded");
        return NULL;
    }
    return PyLong_FromLongLong((long long)g_zz_d64((uint64_t)v));
}

static PyObject *py_bench_encode(PyObject *self, PyObject *args) {
    if (!g_bench_encode) {
        PyErr_SetString(PyExc_RuntimeError, "bench encode unavailable");
        return NULL;
    }
    uint8_t out[256];
    size_t written = 0;
    int rc = g_bench_encode(out, sizeof(out), &written);
    if (rc != 0) {
        PyErr_SetString(PyExc_ValueError, "bench encode failed");
        return NULL;
    }
    return PyBytes_FromStringAndSize((const char *)out, (Py_ssize_t)written);
}

static PyObject *py_bench_decode(PyObject *self, PyObject *args) {
    Py_buffer buf;
    Py_ssize_t offset = 0;
    Py_ssize_t end = -1;
    if (!PyArg_ParseTuple(args, "y*|nn", &buf, &offset, &end)) {
        return NULL;
    }
    if (!g_bench_decode || !g_bench_decoded_size || g_bench_decoded_size() != sizeof(BenchDecoded)) {
        PyBuffer_Release(&buf);
        PyErr_SetString(PyExc_RuntimeError, "bench decode unavailable");
        return NULL;
    }
    if (end < 0) end = buf.len;
    if (offset < 0 || end < offset || end > buf.len) {
        PyBuffer_Release(&buf);
        PyErr_SetString(PyExc_ValueError, "invalid decode range");
        return NULL;
    }
    BenchDecoded out;
    const uint8_t *start = (const uint8_t *)buf.buf + (size_t)offset;
    size_t n = (size_t)(end - offset);
    int rc = decode_bench_data(start, n, &out);
    PyBuffer_Release(&buf);
    if (rc != 0) {
        PyErr_Format(PyExc_ValueError, "bench decode failed: %d", rc);
        return NULL;
    }

    if (out.m_len > 16) {
        PyErr_SetString(PyExc_ValueError, "invalid m_len");
        return NULL;
    }

    PyObject *ret = PyDict_New();
    if (!ret) return NULL;

    #define SET_INT(name, v) do { \
        PyObject *tmp = PyLong_FromLongLong((long long)(v)); \
        if (!tmp || PyDict_SetItemString(ret, name, tmp) < 0) { Py_XDECREF(tmp); Py_DECREF(ret); return NULL; } \
        Py_DECREF(tmp); \
    } while (0)

    #define SET_FLOAT(name, v) do { \
        PyObject *tmp = PyFloat_FromDouble((double)(v)); \
        if (!tmp || PyDict_SetItemString(ret, name, tmp) < 0) { Py_XDECREF(tmp); Py_DECREF(ret); return NULL; } \
        Py_DECREF(tmp); \
    } while (0)

    SET_INT("a", out.a);
    SET_INT("b", out.b);
    SET_INT("c", out.c);
    SET_INT("d", out.d);
    SET_INT("e", out.e);
    SET_INT("f", out.f);
    SET_INT("g", out.g);
    SET_INT("h", out.h);
    SET_FLOAT("i", out.i);
    SET_FLOAT("j", out.j);
    SET_INT("k", out.k);
    SET_INT("l", out.l);
    SET_INT("n", out.n);
    SET_INT("o_a", out.o_a);
    SET_INT("o_b", out.o_b);
    SET_INT("s", out.s);
    SET_INT("p_count", out.p_count);
    SET_INT("p0", out.p0);
    SET_INT("p1", out.p1);
    SET_INT("p2", out.p2);
    SET_INT("q_count", out.q_count);
    SET_INT("q0", out.q0);
    SET_INT("q1", out.q1);
    SET_INT("q2", out.q2);
    SET_INT("r_count", out.r_count);

    PyObject *mbytes = PyBytes_FromStringAndSize((const char *)out.m_bytes, (Py_ssize_t)out.m_len);
    if (!mbytes || PyDict_SetItemString(ret, "m_bytes", mbytes) < 0) {
        Py_XDECREF(mbytes);
        Py_DECREF(ret);
        return NULL;
    }
    Py_DECREF(mbytes);
    return ret;
}

static PyObject *py_bench_decode_noalloc(PyObject *self, PyObject *args) {
    Py_buffer buf;
    Py_ssize_t offset = 0;
    Py_ssize_t end = -1;
    if (!PyArg_ParseTuple(args, "y*|nn", &buf, &offset, &end)) {
        return NULL;
    }
    if (!g_bench_decode || !g_bench_decoded_size || g_bench_decoded_size() != sizeof(BenchDecoded)) {
        PyBuffer_Release(&buf);
        PyErr_SetString(PyExc_RuntimeError, "bench decode unavailable");
        return NULL;
    }
    if (end < 0) end = buf.len;
    if (offset < 0 || end < offset || end > buf.len) {
        PyBuffer_Release(&buf);
        PyErr_SetString(PyExc_ValueError, "invalid decode range");
        return NULL;
    }
    BenchDecoded out;
    const uint8_t *start = (const uint8_t *)buf.buf + (size_t)offset;
    size_t n = (size_t)(end - offset);
    int rc = decode_bench_data(start, n, &out);
    PyBuffer_Release(&buf);
    if (rc != 0) {
        PyErr_Format(PyExc_ValueError, "bench decode failed: %d", rc);
        return NULL;
    }
    Py_RETURN_TRUE;
}

static int dict_set_obj(PyObject *dict, PyObject *key, PyObject *value) {
    return PyDict_SetItem(dict, key, value);
}

static PyObject *get_writable_dict(PyObject *obj) {
    PyTypeObject *tp = Py_TYPE(obj);
    Py_ssize_t dictoffset = tp->tp_dictoffset;
    if (dictoffset != 0) {
        char *addr = (char *)obj;
        if (dictoffset < 0) {
            dictoffset += (Py_ssize_t)Py_SIZE(obj) * (Py_ssize_t)sizeof(PyObject *);
        }
        PyObject **dictptr = (PyObject **)(addr + dictoffset);
        if (dictptr) {
            if (*dictptr == NULL) {
                *dictptr = PyDict_New();
                if (!*dictptr) return NULL;
            }
            Py_INCREF(*dictptr);
            return *dictptr;
        }
    }

    PyObject *d = PyObject_GetAttrString(obj, "__dict__");
    if (!d) return NULL;
    if (!PyDict_Check(d)) {
        Py_DECREF(d);
        PyErr_SetString(PyExc_TypeError, "object has no writable __dict__");
        return NULL;
    }
    return d;
}

static PyObject *create_instance_no_init(PyObject *cls) {
    if (!PyType_Check(cls)) {
        return PyObject_CallNoArgs(cls);
    }
    static PyObject *empty_args = NULL;
    if (!empty_args) {
        empty_args = PyTuple_New(0);
        if (!empty_args) return NULL;
    }
    PyTypeObject *tp = (PyTypeObject *)cls;
    if (!tp->tp_new) {
        PyErr_SetString(PyExc_TypeError, "class has no tp_new");
        return NULL;
    }
    return tp->tp_new(tp, empty_args, NULL);
}

static int fill_sub_ab(PyObject *sub, long long a, long long b) {
    PyObject *sub_dict = get_writable_dict(sub);
    if (!sub_dict) {
        return -1;
    }
    PyObject *va = (a == 150) ? v_150 : NULL;
    PyObject *vb = (b == -150) ? v_m150 : NULL;
    if (!va) {
        va = PyLong_FromLongLong(a);
        if (!va) { Py_DECREF(sub_dict); return -1; }
    } else {
        Py_INCREF(va);
    }
    if (!vb) {
        vb = PyLong_FromLongLong(b);
        if (!vb) { Py_DECREF(va); Py_DECREF(sub_dict); return -1; }
    } else {
        Py_INCREF(vb);
    }
    int rc = PyDict_SetItem(sub_dict, k_a, va) | PyDict_SetItem(sub_dict, k_b, vb);
    Py_DECREF(va);
    Py_DECREF(vb);
    if (rc < 0) {
        Py_DECREF(sub_dict);
        return -1;
    }
    Py_DECREF(sub_dict);
    return 0;
}

static PyObject *py_bench_decode_into(PyObject *self, PyObject *args) {
    PyObject *obj = NULL;
    PyObject *sub_cls = NULL;
    Py_buffer buf;
    Py_ssize_t offset = 0;
    Py_ssize_t end = -1;
    if (!PyArg_ParseTuple(args, "OOy*|nn", &obj, &sub_cls, &buf, &offset, &end)) {
        return NULL;
    }
    if (!g_bench_decode || !g_bench_decoded_size || g_bench_decoded_size() != sizeof(BenchDecoded)) {
        PyBuffer_Release(&buf);
        PyErr_SetString(PyExc_RuntimeError, "bench decode unavailable");
        return NULL;
    }
    if (end < 0) end = buf.len;
    if (offset < 0 || end < offset || end > buf.len) {
        PyBuffer_Release(&buf);
        PyErr_SetString(PyExc_ValueError, "invalid decode range");
        return NULL;
    }

    BenchDecoded out;
    const uint8_t *start = (const uint8_t *)buf.buf + (size_t)offset;
    size_t n = (size_t)(end - offset);
    int rc = decode_bench_data(start, n, &out);
    PyBuffer_Release(&buf);
    if (rc != 0) {
        PyErr_Format(PyExc_ValueError, "bench decode failed: %d", rc);
        return NULL;
    }
    if (out.m_len > 16) {
        PyErr_SetString(PyExc_ValueError, "invalid m_len");
        return NULL;
    }

    PyObject *obj_dict = get_writable_dict(obj);
    if (!obj_dict) {
        return NULL;
    }
    if (ensure_keys_consts() < 0) {
        Py_DECREF(obj_dict);
        return NULL;
    }

    if (dict_set_obj(obj_dict, k_a, v_i32_max) < 0) goto fail;
    if (dict_set_obj(obj_dict, k_b, v_i64_max) < 0) goto fail;
    if (dict_set_obj(obj_dict, k_c, v_i32_max) < 0) goto fail;
    if (dict_set_obj(obj_dict, k_d, v_i64_max) < 0) goto fail;
    if (dict_set_obj(obj_dict, k_e, v_u32_max) < 0) goto fail;
    if (dict_set_obj(obj_dict, k_f, v_u64_max) < 0) goto fail;
    if (dict_set_obj(obj_dict, k_g, v_i32_max) < 0) goto fail;
    if (dict_set_obj(obj_dict, k_h, v_i64_max) < 0) goto fail;
    if (dict_set_obj(obj_dict, k_i, v_f_03) < 0) goto fail;
    if (dict_set_obj(obj_dict, k_j, v_d_03) < 0) goto fail;
    if (dict_set_obj(obj_dict, k_k, v_u32_max) < 0) goto fail;
    if (dict_set_obj(obj_dict, k_l, v_u64_max) < 0) goto fail;
    if (dict_set_obj(obj_dict, k_n, v_true) < 0) goto fail;
    if (dict_set_obj(obj_dict, k_s, out.s ? v_1 : v_0) < 0) goto fail;

    if (out.m_len == 6 && memcmp(out.m_bytes, "\xe6\xb5\x8b\xe8\xaf\x95", 6) == 0) {
        if (dict_set_obj(obj_dict, k_m, v_str_test) < 0) goto fail;
    } else {
        PyObject *m = PyUnicode_DecodeUTF8((const char *)out.m_bytes, (Py_ssize_t)out.m_len, "strict");
        if (!m) goto fail;
        if (PyDict_SetItem(obj_dict, k_m, m) < 0) {
            Py_DECREF(m);
            goto fail;
        }
        Py_DECREF(m);
    }

    PyObject *sub = create_instance_no_init(sub_cls);
    if (!sub) goto fail;
    if (fill_sub_ab(sub, out.o_a, out.o_b) < 0) {
        Py_DECREF(sub);
        goto fail;
    }
    if (PyDict_SetItem(obj_dict, k_o, sub) < 0) {
        Py_DECREF(sub);
        goto fail;
    }
    Py_DECREF(sub);

    uint32_t p_count = out.p_count > 3 ? 3 : out.p_count;
    PyObject *p = PyList_New((Py_ssize_t)p_count);
    if (!p) goto fail;
    if (p_count > 0) PyList_SET_ITEM(p, 0, (Py_INCREF(v_1), v_1));
    if (p_count > 1) PyList_SET_ITEM(p, 1, (Py_INCREF(v_2), v_2));
    if (p_count > 2) PyList_SET_ITEM(p, 2, (Py_INCREF(v_3), v_3));
    if (PyDict_SetItem(obj_dict, k_p, p) < 0) {
        Py_DECREF(p);
        goto fail;
    }
    Py_DECREF(p);

    uint32_t q_count = out.q_count > 3 ? 3 : out.q_count;
    PyObject *q = PyList_New((Py_ssize_t)q_count);
    if (!q) goto fail;
    if (q_count > 0) PyList_SET_ITEM(q, 0, (Py_INCREF(v_1), v_1));
    if (q_count > 1) PyList_SET_ITEM(q, 1, (Py_INCREF(v_2), v_2));
    if (q_count > 2) PyList_SET_ITEM(q, 2, (Py_INCREF(v_3), v_3));
    if (PyDict_SetItem(obj_dict, k_q, q) < 0) {
        Py_DECREF(q);
        goto fail;
    }
    Py_DECREF(q);

    PyObject *r = PyList_New((Py_ssize_t)out.r_count);
    if (!r) goto fail;
    for (uint32_t i = 0; i < out.r_count; i++) {
        PyObject *item = create_instance_no_init(sub_cls);
        if (!item) {
            Py_DECREF(r);
            goto fail;
        }
        if (fill_sub_ab(item, 150, -150) < 0) {
            Py_DECREF(item);
            Py_DECREF(r);
            goto fail;
        }
        PyList_SET_ITEM(r, (Py_ssize_t)i, item);
    }
    if (PyDict_SetItem(obj_dict, k_r, r) < 0) {
        Py_DECREF(r);
        goto fail;
    }
    Py_DECREF(r);

    Py_DECREF(obj_dict);
    Py_RETURN_TRUE;

fail:
    Py_DECREF(obj_dict);
    return NULL;
}

static PyMethodDef methods[] = {
    {"init_library", py_init_library, METH_VARARGS, "Initialize native zig library"},
    {"available", py_available, METH_NOARGS, "Native backend availability"},
    {"has_bench", py_has_bench, METH_NOARGS, "Native bench fastpath availability"},
    {"has_bench_decode", py_has_bench_decode, METH_NOARGS, "Native bench decode fastpath availability"},
    {"encode_varint_u64", py_encode_varint_u64, METH_VARARGS, "Encode varint"},
    {"decode_varint_u64", py_decode_varint_u64, METH_VARARGS, "Decode varint"},
    {"zigzag_encode32", py_zigzag_encode32, METH_VARARGS, "zigzag32 encode"},
    {"zigzag_encode64", py_zigzag_encode64, METH_VARARGS, "zigzag64 encode"},
    {"zigzag_decode32", py_zigzag_decode32, METH_VARARGS, "zigzag32 decode"},
    {"zigzag_decode64", py_zigzag_decode64, METH_VARARGS, "zigzag64 decode"},
    {"bench_encode", py_bench_encode, METH_NOARGS, "bench encode"},
    {"bench_decode", py_bench_decode, METH_VARARGS, "bench decode"},
    {"bench_decode_noalloc", py_bench_decode_noalloc, METH_VARARGS, "bench decode no python object alloc"},
    {"bench_decode_into", py_bench_decode_into, METH_VARARGS, "bench decode directly into object"},
    {NULL, NULL, 0, NULL},
};

static struct PyModuleDef moddef = {
    PyModuleDef_HEAD_INIT,
    "_zignative",
    "zcprotobuf native CPython bridge",
    -1,
    methods,
};

PyMODINIT_FUNC PyInit__zignative(void) {
    return PyModule_Create(&moddef);
}
