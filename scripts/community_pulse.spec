# -*- mode: python ; coding: utf-8 -*-
a=Analysis(['app/main.py'],pathex=['.'],datas=[('assets','assets')],hiddenimports=['sqlalchemy.dialects.sqlite'],hookspath=[],excludes=[])
pyz=PYZ(a.pure);exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name='CommunityPulseAI',console=False,icon=None)
