from setuptools import setup
from setuptools.command.build_ext import build_ext as _build_ext
from setuptools.extension import Extension


class build_ext(_build_ext):
    def build_extension(self, ext):
        for i, extra in enumerate(ext.extra_objects):
            if isinstance(extra, Extension):
                sources = sorted(extra.sources)
                extra_args = extra.extra_compile_args or []
                macros = extra.define_macros[:]
                for undef in extra.undef_macros:
                    macros.append((undef,))
                objects = self.compiler.compile(
                    sources,
                    output_dir=self.build_temp,
                    macros=macros,
                    include_dirs=extra.include_dirs,
                    debug=self.debug,
                    extra_postargs=extra_args,
                    depends=extra.depends,
                )
                ext.extra_objects[i] = objects[0]
        return super().build_extension(ext)

setup(
    cmdclass={'build_ext': build_ext},
    cffi_modules=[
        './ada_url/ada_build.py:ffi_builder',
    ],
)
