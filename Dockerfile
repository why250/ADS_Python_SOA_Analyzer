# 使用 CentOS 7 系统 (为了兼容 RHEL 7.9)
FROM centos:7

# 1. 换源，解决 CentOS 7 停止维护导致无法下载的问题
RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-* && \
    sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*

# 2. 安装编译工具和图形库依赖 (PyInstaller 打包 PyQt5 需要这些)
RUN yum -y update && yum -y groupinstall "Development Tools" && \
    yum -y install wget openssl-devel bzip2-devel libffi-devel \
    mesa-libGL-devel libX11-devel libxkbcommon-x11-devel libXext-devel && \
    yum clean all

# 3. 下载并安装 Python 3.9.18
WORKDIR /usr/src
RUN wget https://www.python.org/ftp/python/3.9.18/Python-3.9.18.tgz && \
    tar xzf Python-3.9.18.tgz && \
    cd Python-3.9.18 && \
    ./configure --enable-optimizations && \
    make altinstall && \
    rm -f /usr/src/Python-3.9.18.tgz

# 4. 设置 python3 命令
RUN ln -s /usr/local/bin/python3.9 /usr/bin/python3 && \
    ln -s /usr/local/bin/pip3.9 /usr/bin/pip3

# 5. 安装 PyInstaller 和你的依赖
RUN pip3 install --upgrade pip
RUN pip3 install pyinstaller
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

# 6. 设置工作目录
WORKDIR /app