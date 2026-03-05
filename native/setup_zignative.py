from setuptools import Extension, setup

setup(
    name="zcprotobuf_zignative",
    packages=[],
    py_modules=[],
    ext_modules=[
        Extension(
            "zcprotobuf._zignative",
            sources=["zcprotobuf/native/zignative.c"],
        )
    ],
)
