# bcm-slurm-builder
Tool to build slurm packages for use in a BCM cluster.

# Contribution Guidelines
`bcm-slurm-builder` follows internal roadmaps and development priorities. Contributions from the community are welcome
but, in order for them to be accepted, they need to fit within the project's internal goals.

If you want to read more about how to contribute to the project, please, check [CONTRIBUTING.md](CONTRIBUTING.md).

## Security
- To make a Vulnerability disclosure, check [SECURITY.md](SECURITY.md).
- Do not file public issues for security reports.

# Overview
BCM clusters use custom-built slurm packages. This project allows
building slurm packages for BCM clusters from upstream code.

# Requirements
- A BCM 11.0 cluster.

## BCM cluster distros
- RHEL9
- Ubuntu 22.04
- Ubuntu 24.04

## Slurm versions
- 25.11.x

# Usage
Download the project's tarball and expand it somewhere in the cluster's head node.

Place yourself inside the directory of the `bcm slurm builder` project. Then run the script `./build.sh`
providing the slurm version you would like to build as a parameter. The build process will take care
of downloading the slurm source tarball and installing the necessary dependencies to be able to carry out
building the packages. When the process is finished, the resulting packages will be in the same directory
where `./build.sh` was called from.

Building on compute nodes is **not** supported at the time.

## Sample run
Here's one sample run using a BCM 11.32.0 cluster running on Ubuntu 24.04.

```
root@u24-slurm-builder:~/bcm-slurm-builder# ls -l
total 16
-rwxrwxr-x 1 root root 6512 Apr 13 06:09 build.sh
drwxrwxr-x 3 root root   25 Apr 13 06:09 deb
-rw-rw-r-- 1 root root  959 Apr 13 06:09 dependencies.json
drwxrwxr-x 2 root root  180 Apr 13 06:09 pyxis
drwxrwxr-x 2 root root   29 Apr 13 06:09 rpm
drwxrwxr-x 2 root root   87 Apr 13 06:09 scripts
drwxrwxr-x 3 root root 4096 Apr 13 06:09 slurm_files
root@u24-slurm-builder:~/bcm-slurm-builder# ./build.sh 25.11.5
+ . /etc/os-release
++ PRETTY_NAME='Ubuntu 24.04.3 LTS'
++ NAME=Ubuntu
++ VERSION_ID=24.04
++ VERSION='24.04.3 LTS (Noble Numbat)'
++ VERSION_CODENAME=noble
++ ID=ubuntu
++ ID_LIKE=debian
++ HOME_URL=https://www.ubuntu.com/
++ SUPPORT_URL=https://help.ubuntu.com/
++ BUG_REPORT_URL=https://bugs.launchpad.net/ubuntu/
++ PRIVACY_POLICY_URL=https://www.ubuntu.com/legal/terms-and-policies/privacy-policy
++ UBUNTU_CODENAME=noble
++ LOGO=ubuntu-logo
.
.
.
dpkg-deb: building package 'slurm25.11-libpmi' in '../slurm25.11-libpmi_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb'.
dpkg-deb: building package 'slurm25.11-prs' in '../slurm25.11-prs_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb'.
+ '[' 0 -ne 0 ']'
+ cd -
/root/bcm-slurm-builder
+ set +x
slurm25.11_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
slurm25.11-contribs_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
slurm25.11-devel_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
slurm25.11-libpmi_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
slurm25.11-openlava_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
slurm25.11-pam_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
slurm25.11-perlapi_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
slurm25.11-prs_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
slurm25.11-sackd_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
slurm25.11-slurmctld_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
slurm25.11-slurmd_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
slurm25.11-slurmdbd_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
slurm25.11-slurmrestd_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
slurm25.11-torque_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
root@u24-slurm-builder:~/bcm-slurm-builder# ls -l *.deb
-rw-r--r-- 1 root root 63186972 Apr 15 05:01 slurm25.11_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
-rw-r--r-- 1 root root    12202 Apr 15 05:01 slurm25.11-contribs_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
-rw-r--r-- 1 root root    76814 Apr 15 05:01 slurm25.11-devel_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
-rw-r--r-- 1 root root   258832 Apr 15 05:01 slurm25.11-libpmi_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
-rw-r--r-- 1 root root     6708 Apr 15 05:01 slurm25.11-openlava_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
-rw-r--r-- 1 root root   151694 Apr 15 05:01 slurm25.11-pam_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
-rw-r--r-- 1 root root   914528 Apr 15 05:01 slurm25.11-perlapi_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
-rw-r--r-- 1 root root   930466 Apr 15 05:01 slurm25.11-prs_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
-rw-r--r-- 1 root root   100420 Apr 15 05:01 slurm25.11-sackd_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
-rw-r--r-- 1 root root  1727272 Apr 15 05:01 slurm25.11-slurmctld_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
-rw-r--r-- 1 root root   445422 Apr 15 05:01 slurm25.11-slurmd_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
-rw-r--r-- 1 root root   211380 Apr 15 05:01 slurm25.11-slurmdbd_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
-rw-r--r-- 1 root root   183122 Apr 15 05:01 slurm25.11-slurmrestd_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
-rw-r--r-- 1 root root   128048 Apr 15 05:01 slurm25.11-torque_25.11.5-200001-cm11.0-5bf9efcb4e_amd64.deb
```

# License
This project is licensed under the [Apache 2.0 License](LICENSE-apache2.0.txt) - Check [LICENSING.md](LICENSING.md) for details.
