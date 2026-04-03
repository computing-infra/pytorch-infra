  docker run -it --rm \
      --name npu-test \
      --user root \
      --device /dev/davinci5 \
      --device /dev/davinci_manager \
      --device /dev/devmm_svm \
      --device /dev/hisi_hdc \
      -v /usr/local/sbin/npu-smi:/usr/local/sbin/npu-smi \
      -v /usr/local/Ascend/driver:/usr/local/Ascend/driver \
      -v /usr/local/Ascend/firmware:/usr/local/Ascend/firmware \
      swr.cn-north-4.myhuaweicloud.com/frameworkptadapter/pytorch_2.11.0_a2_aarch64_builder:20260331 \
      /bin/bash


pip3.11 uninstall -y torch torchvision

pip3.11 install --pre "torch==2.12.0.dev20260217" --index-url https://download.pytorch.org/whl/nightly/cpu


git clone --depth=1 --recurse-submodules  https://gitcode.com/Ascend/pytorch.git ascend_pytorch

cd ascend_pytorch

 bash ci/build.sh --python=3.11

pip3.11 install ascend_pytorch/dist/torch_npu*.whl

          # 加载 CANN 环境变量
source /usr/local/Ascend/cann/set_env.sh 2>/dev/null || true
source /usr/local/Ascend/nnal/atb/set_env.sh 2>/dev/null || true

python3.11 -c "import torch; print(f'torch: {torch.__version__}'); import torch_npu; print(f'torch_npu: {torch_npu.__version__}'); print(f'NPU available: {torch.npu.is_available()}'); print(f'NPU count: {torch.npu.device_count()}'); print(f'NPU name: {torch.npu.get_device_name(0) if torch.npu.is_available() else \"N/A\"}')"


