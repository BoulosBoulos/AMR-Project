from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'amr_robot_description'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),

        # Install URDF/xacro files
        (os.path.join('share', package_name, 'urdf'),
            glob('urdf/*.urdf.xacro')),
        (os.path.join('share', package_name, 'urdf'),
            glob('urdf/*.urdf')),

        # Install SDF model directory (service_robot/model.sdf + model.config)
        (os.path.join('share', package_name, 'models', 'service_robot'),
            glob('models/service_robot/model.*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='vboxuser',
    maintainer_email='student@aub.edu.lb',
    description='AMR Final Project - amr_robot_description (SDF model + URDF/xacro)',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)
