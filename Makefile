#
# Makefile for creating a PyCmd.zip binary distribution
# Requires:
#	* Python >= 2.7 (32-bit or 64-bit)
#	* MinGW (make, rm, cp etc) and python in the %PATH%
#	* cx_freeze, pywin32 and pefile installed in the Python dist
#
# Author: Horea Haitonic
#
RM = rm -f
CP = cp
MV = mv
ZIP = "C:\Program Files\7-Zip\7z.exe"
SHELL = cmd

SRC = PyCmd.py InputState.py DirHistory.py common.py completion.py console.py fsm.py
SRC_TEST = common_tests.py

PYTHONHOME_W64 = C:\python\Python27

PYTHON_W64 = (set PYTHONHOME=$(PYTHONHOME_W64)) && "$(PYTHONHOME_W64)\python.exe"

ifndef BUILD_VERSION
	BUILD_VERSION = $(shell cat setup.py | grep "version.*=" | grep -o '[0-9.]*')
endif

ifndef BUILD_DATE
	BUILD_DATE = $(shell WMIC os GET LocalDateTime | grep -v Local | cut -c 1-8)
endif

.PHONY: all
all: 
	$(MAKE) clean
	$(MAKE) dist_w64

doc: pycmd_public.py
	$(PYTHON_W64) -c "import pycmd_public, pydoc; pydoc.writedoc('pycmd_public')"

dist_w64: clean $(SRC) doc
	echo build_version = '$(BUILD_VERSION)' > buildinfo.py
	echo build_date = '$(BUILD_DATE)' >> buildinfo.py
	$(PYTHON_W64) setup.py build
	$(MV) build\exe.win-amd64-2.7 PyCmd
	$(CP) README.txt PyCmd
# cx_freeze on Py64 copies the wrong pywintypes27.dll, overwrite it here:
	$(CP) $(PYTHONHOME_W64)\Lib\site-packages\pywin32_system32\pywintypes27.dll PyCmd\lib
	(echo Release $(BUILD_VERSION) $(BUILD_DATE): && echo. && type NEWS.txt) > PyCmd\NEWS.txt
	$(ZIP) -r PyCmd-$(BUILD_VERSION)-$(BUILD_DATE)-w64.zip PyCmd

.PHONY: clean
clean:
	$(RM) buildinfo.*
	$(RM) $(SRC:%.py=%.pyc)
	$(RM) pycmd_public.html
	cd tests && $(RM) $(SRC_TEST:%.py=%.pyc) && $(RM) __init__.pyc
	$(RM) -r build PyCmd

