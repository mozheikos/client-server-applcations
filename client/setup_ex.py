import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    'packages': ['common', 'db', 'gui', 'log', 'templates']
}
setup(
    name='messenger_client',
    version='0.1.0',
    description='Client for messenger',
    options={
        'build_exe': build_exe_options
    },
    executables=[
        Executable(
            'launcher_client.py',
            base='',
            targetName='client_launcher'
        )
    ]
)