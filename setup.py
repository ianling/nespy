from distutils.core import setup
from Cython.Build import cythonize


# python3 setup.py build_ext --inplace
# cythonize -3 -a -i .\nespy\utils.py .\nespy\cpu.py .\nespy\ppu.py .\nespy\clock.py .\nespy\nes.py .\nespy\apu.py .\nespy\enums.py
setup(ext_modules=cythonize(['nespy/nes.py', 'nespy/apu.py', 'nespy/clock.py',
                             'nespy/cpu.py', 'nespy/ppu.py', 'nespy/enums.py',
                             'nespy/utils.py', 'nespy/exceptions.py'],
                            language_level='3', annotate=True))
