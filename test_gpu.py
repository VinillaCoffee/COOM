import tensorflow as tf
#检查tensor版本
print(tf.__version__)
#查询tf库的路径
print("TensorFlow Filepath:", tf.__file__)
#检查GPU设备
print("GPU Device:", tf.config.list_physical_devices('GPU'))
#检查GPU是否可用
if tf.test.is_gpu_available():
    print("GPU is available")
else:
    print("GPU is not available")

