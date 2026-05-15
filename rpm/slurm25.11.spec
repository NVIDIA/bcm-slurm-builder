%define cmrelease   %(bc-branch-dependency-name)
%define release     %(bc-revision-number)_%(bc-release-tag)

%define rhel8_based %(test -e /etc/os-release && source /etc/os-release && echo "${ID}  ${VERSION_ID}" | grep -q -E "^(rhel|centos|rocky)  8" && echo 1 || echo 0)
%define rhel9_based %(test -e /etc/os-release && source /etc/os-release && echo "${ID}  ${VERSION_ID}" | grep -q -E "^(rhel|centos|rocky)  9" && echo 1 || echo 0)
%define sles15      %(test -e /etc/os-release && source /etc/os-release && echo "${ID}  ${VERSION}" | grep -q "^sles  15" && echo 1 || echo 0)
%define use_prs     %(test -f /root/rpmbuild/SOURCES/prs-select.patch && echo 1 || echo 0)

%define arch_name   %(arch)
%define aarch64     %(test %{arch_name} == 'aarch64' && echo 1 || echo 0)

%define major_slurm_version 25.11

%define _root              /cm/local/apps/slurm
%define _vardir            %{_root}/var
%define _prefix            %{_root}/%{major_slurm_version}
%define _current_link      %{_root}/current
%define _mandir            %{_prefix}/man
%define _docsdir           %{_prefix}/share/doc
%define _scriptsdir        %{_prefix}/scripts
%define _libdir            %{_prefix}/lib64
%define _templatesdir      %{_prefix}/templates
%define _cmdir             %{_vardir}/cm
%define _allpostjobsdir    %{_vardir}/pre-post-job-logs/all-post-jobs
%define _allprejobsdir     %{_vardir}/pre-post-job-logs/all-pre-jobs
%define _failedpostjobsdir %{_vardir}/pre-post-job-logs/failed-post-jobs
%define _failedprejobsdir  %{_vardir}/pre-post-job-logs/failed-pre-jobs
%define _prologsdir        %{_vardir}/prologs
%define _epilogsdir        %{_vardir}/epilogs
%define _spooldir          %{_vardir}/spool
%define _unitdir           /usr/lib/systemd/system/
%define _sysconfigdir      /etc/sysconfig

# Disable hardened builds. -z,now or -z,relro breaks the plugin stack
%undefine _hardened_build
%global _hardened_cflags "-Wl,-z,lazy"
%global _hardened_ldflags "-Wl,-z,lazy"

%if %{rhel9_based}
# Disable Link Time Optimization (LTO)
%define _lto_cflags %{nil}
%endif

%define _build_id_links none

Name:    slurm%{major_slurm_version}
Version: 25.11.5
Release: %{release}

Summary: Slurm Workload Management

License: GPLv2+
Group: System Environment/Base
Source: slurm-%{version}.tar.bz2
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}
URL: http://slurm.schedmd.com
Packager: dev <dev@brightcomputing.com>

Provides: slurm = %{major_slurm_version}
Conflicts: slurm < %{major_slurm_version}

Patch0: slurm-modules.patch
Patch1: scontrol.patch
%if %{use_prs}
Patch2: prs-select.patch
Patch3: autoconf-fix.patch
%endif
Patch4: systemd-units.patch

Requires: cm-config-cm = %{cmrelease}

BuildRequires: gtk2-devel >= 2.7.1
BuildRequires: ncurses-devel
BuildRequires: pkgconfig
BuildRequires: lua
BuildRequires: lua-devel
BuildRequires: munge-devel
BuildRequires: libjwt-devel

BuildRequires: cm-ucx-local
BuildRequires: cm-pmix4-local
BuildRequires: cm-pmix3-local
BuildRequires: cm-hdf5

%if %{sles15}
BuildRequires: cm-libjwt
BuildRequires: libjson-c-devel
BuildRequires: python
BuildRequires: kernel-devel, dbus-1-devel
%else
BuildRequires: python3
BuildRequires: kernel-headers, dbus-devel
BuildRequires: json-c-devel
%endif

%description
Slurm is an open source, fault-tolerant, and highly scalable
cluster management and job scheduling system for Linux clusters.
Components include machine status, partition management,
job management, scheduling and accounting modules.

# Never allow rpm to strip binaries as this will break
#  parallel debugging capability
%define __os_install_post /usr/lib/rpm/brp-compress
%define debug_package %{nil}

# Should unpackaged files in a build root terminate a build?
# Note: The default value should be 0 for legacy compatibility.
# This was added due to a bug in Suse Linux. For a good reference, see
# http://slforums.typo3-factory.net/index.php?showtopic=11378
%define _unpackaged_files_terminate_build      0

# First we remove $prefix/local and then just prefix to make
# sure we get the correct installdir
%define _perlarch %(perl -e 'use Config; $T=$Config{installsitearch}; $P=$Config{installprefix}; $P1="$P/local"; $T =~ s/$P1//; $T =~ s/$P//; print $T;')
%define _perlman3 %(perl -e 'use Config; $T=$Config{installsiteman3dir}; $P=$Config{siteprefix}; $P1="$P/local"; $T =~ s/$P1//; $T =~ s/$P//; $T =~ s/share\//; print $T;')
%define _perlarchlib %(perl -e 'use Config; $T=$Config{installarchlib}; $P=$Config{installprefix}; $P1="$P/local"; $T =~ s/$P1//; $T =~ s/$P//; print $T;')

%define _perldir %{_prefix}%{_perlarch}
%define _perlman3dir %{_prefix}%{_perlman3}
%define _perlarchlibdir %{_prefix}%{_perlarchlib}
#############################################################################

%package perlapi
Summary: Perl API to Slurm.
Group: Development/System
Provides: slurm-perlapi = %{major_slurm_version}
Requires: cm-config-cm = %cmrelease
Requires: %{name}
Conflicts: slurm-perlapi < %{major_slurm_version}
%description perlapi
Perl API package for Slurm.  This package includes the perl API to provide a
helpful interface to Slurm through Perl.

%package prs
Summary: Slurm Module to support PRS
Provides: slurm-prs = %{major_slurm_version}
Requires: cm-config-cm = %cmrelease
Requires: %{name}
Conflicts: slurm-prs < %{major_slurm_version}
%description prs
This package includes the binary that provides select_gnl_cons_tres.so plugin.

%package devel
Summary: Development package for Slurm.
Group: Development/System
Provides: slurm-devel = %{major_slurm_version}
Requires: cm-config-cm = %cmrelease
Requires: %{name}
Conflicts: slurm-devel < %{major_slurm_version}
%description devel
Development package for Slurm.  This package includes the header files
and static libraries for the Slurm API.

%package slurmctld
Summary: Slurm controller daemon
Group: System Environment/Base
Provides: slurm-slurmctld = %{major_slurm_version}
Conflicts: slurm-slurmctld < %{major_slurm_version}
Requires: cm-config-cm = %cmrelease
Requires: %{name}
Requires: munge
%if %{sles15}
Requires: libssh2-1
%else
Requires: libssh2
%endif
%description slurmctld
Slurm controller daemon. Used to manage the job queue, schedule jobs,
and dispatch RPC messages to the slurmd processon the compute nodes
to launch jobs.

%package slurmd
Summary: Slurm compute node daemon
Group: System Environment/Base
Provides: slurm-slurmd = %{major_slurm_version}
Conflicts: slurm-slurmd < %{major_slurm_version}
Requires: cm-config-cm = %cmrelease
Requires: %{name}
Requires: munge
%description slurmd
Slurm compute node daemon. Used to launch jobs on compute nodes.

%package slurmdbd
Summary: Slurm database daemon
Group: System Environment/Base
Provides: slurm-slurmdbd = %{major_slurm_version}
Requires: cm-config-cm = %cmrelease
Requires: %{name}
Conflicts: slurm-slurmdbd < %{major_slurm_version}
%description slurmdbd
Slurm database daemon. Used to accept and process database RPCs and upload
database changes to slurmctld daemons on each cluster

%package libpmi
Summary: Slurm\'s implementation of the pmi libraries
Group: System Environment/Base
Requires: cm-config-cm = %cmrelease
Requires: %{name}
Conflicts: pmix-libpmi
%description libpmi
Slurm\'s version of libpmi. For systems using Slurm, this version
is preferred over the compatibility libraries shipped by the PMIx project.

%package torque
Summary: Torque/PBS wrappers for transitition from Torque/PBS to Slurm.
Group: Development/System
Provides: slurm-torque = %{major_slurm_version}
Requires: slurm-perlapi = %{major_slurm_version}
Requires: cm-config-cm = %cmrelease
Requires: %{name}
Conflicts: slurm-torque < %{major_slurm_version}
%description torque
Torque wrapper scripts used for helping migrate from Torque/PBS to Slurm.

%package openlava
Summary: openlava/LSF wrappers for transitition from OpenLava/LSF to Slurm
Group: Development/System
Provides: slurm-openlava = %{major_slurm_version}
Requires: slurm-perlapi = %{major_slurm_version}
Requires: cm-config-cm = %cmrelease
Requires: %{name}
Conflicts: slurm-openlava < %{major_slurm_version}
%description openlava
OpenLava wrapper scripts used for helping migrate from OpenLava/LSF to Slurm

%package contribs
Summary: Perl tool to print Slurm job state information
Group: Development/System
Provides: slurm-contribs = %{major_slurm_version}
Conflicts: slurm-contribs < %{major_slurm_version}
Requires: cm-config-cm = %cmrelease
Requires: %{name}
%description contribs
seff is a mail program used directly by the Slurm daemons. On completion of a
job, wait for it's accounting information to be available and include that
information in the email body.
sjobexit is a slurm job exit code management tool. It enables users to alter
job exit code information for completed jobs
sjstat is a Perl tool to print Slurm job state information. The output is designed
to give information on the resource usage and availablilty, as well as information
about jobs that are currently active on the machine. This output is built
using the Slurm utilities, sinfo, squeue and scontrol, the man pages for these
utilities will provide more information and greater depth of understanding.

%package pam
Summary: PAM module for restricting access to compute nodes via Slurm.
Group: System Environment/Base
Provides: slurm-pam = %{major_slurm_version}
Requires: slurm-slurmd = %{major_slurm_version}
Requires: cm-config-cm = %cmrelease
Requires: %{name}
Conflicts: slurm-pam < %{major_slurm_version}
BuildRequires: pam-devel
AutoReqProv: no
AutoReq: 0 
%description pam
This module restricts access to compute nodes in a cluster where the Simple
Linux Utility for Resource Managment (Slurm) is in use.  Access is granted
to root, any user with a Slurm-launched job currently running on the node,
or any user who has allocated resources on the node according to the Slurm

%package slurmrestd
Summary: Slurm REST API translator
Group: System Environment/Base
%if %{sles15}
BuildRequires: cm-http-parser
BuildRequires: libjson-c-devel
Requires: cm-http-parser cm-libjwt
%else
Requires: http-parser libjwt
BuildRequires: http-parser-devel
BuildRequires: json-c-devel
%endif
Requires: cm-config-cm = %cmrelease
Requires: %{name}
%description slurmrestd
Provides a REST interface to Slurm.

%package sackd
Summary: Slurm authentication daemon
Group: System Environment/Base
Requires: cm-config-cm = %cmrelease
Requires: %{name}
%description sackd
Slurm authentication daemon. Used on login nodes that are not running slurmd
daemons to allow authentication to the cluster.
#############################################################################

%prep
%setup -n slurm-%{version}
%patch -P 0 -p 1
%patch -P 1 -p 1

# Copy the directory to have the original module
cp -a src/plugins/select/cons_tres/ src/plugins/select/cons_tres_org/
%if %{use_prs}
%patch -P 2 -p 1
%patch -P 3 -p 0
%endif
autoconf
%patch -P 4 -p 1
#############################################################################

%build
%configure \
       --prefix=%{_prefix} \
       --enable-pkgconfig \
       --with-munge \
       --with-hwloc=/cm/local/apps/hwloc2/current \
       --with-hdf5=/cm/shared/apps/hdf5/current/bin/h5cc \
       --with-pmix=/cm/local/apps/cm-pmix3/current:/cm/local/apps/cm-pmix4/current \
       --with-ucx=/cm/local/apps/ucx/current \
%if %{sles15}
       --with-http-parser=/cm/local/apps/http-parser \
       --with-jwt=/cm/local/apps/libjwt \
%endif
%if ! %{aarch64}
       --with-rsmi=/cm/local/apps/rocm-smi/current/rocm_smi
%endif

make %{?_smp_mflags}
#############################################################################

%check
# Verify main binaries built correctly at a basic level.
./src/slurmctld/slurmctld -V
./src/slurmd/slurmd/slurmd -V

# Run unit tests
make check %{?_smp_mflags}

%install

# Ignore redundant standard rpaths and insecure relative rpaths,
# for RHEL based distros which use "check-rpaths" tool.
export QA_RPATHS=0x5

rm -rf "%{buildroot}"
mkdir -p "%{buildroot}"/etc/logrotate.d/
mkdir -p "%{buildroot}"/etc/slurm/
mkdir -p "%{buildroot}/%{_cmdir}"
mkdir -p "%{buildroot}/%{_docsdir}"
mkdir -p "%{buildroot}/%{_scriptsdir}/power"
mkdir -p "%{buildroot}/%{_perldir}"
mkdir -p "%{buildroot}/%{_perlman3dir}"
mkdir -p "%{buildroot}/%{_prologsdir}"
mkdir -p "%{buildroot}/%{_epilogsdir}"
mkdir -p "%{buildroot}/%{_templatesdir}"
mkdir -p "%{buildroot}/%{_spooldir}"
mkdir -p "%{buildroot}/%{_allpostjobsdir}"
mkdir -p "%{buildroot}/%{_allprejobsdir}"
mkdir -p "%{buildroot}/%{_failedpostjobsdir}"
mkdir -p "%{buildroot}/%{_failedprejobsdir}"

install -m 644 cm-slurm.module         %{buildroot}/%{_templatesdir}/slurm.module.template
install -m 644 cm-slurm.conf           %{buildroot}/%{_templatesdir}/slurm.conf.template
install -m 600 cm-slurmdbd.conf        %{buildroot}/%{_templatesdir}/slurmdbd.conf.template
install -m 644 cm-gres.conf            %{buildroot}/%{_templatesdir}/gres.conf.template
install -m 644 cm-cgroup.conf          %{buildroot}/%{_templatesdir}/cgroup.conf.template

install -m 700 cm-restore-db-password  %{buildroot}/%{_scriptsdir}
install -m 700 cm-slurmrestd-setup     %{buildroot}/%{_scriptsdir}
install -m 700 slurm-backup            %{buildroot}/%{_scriptsdir}
install -m 755 power/*                 %{buildroot}/%{_scriptsdir}/power/

install -m 644 cm-slurmd.logrotate     %{buildroot}/etc/logrotate.d/slurmd
install -m 644 cm-slurmctld.logrotate  %{buildroot}/etc/logrotate.d/slurmctld
install -m 644 cm-slurmdbd.logrotate   %{buildroot}/etc/logrotate.d/slurmdbd

install -m 444 AUTHORS                 %{buildroot}/%{_docsdir}
install -m 444 COPYING                 %{buildroot}/%{_docsdir}
install -m 444 CHANGELOG.md            %{buildroot}/%{_docsdir}
install -m 444 README.md              %{buildroot}/%{_docsdir}
install -m 444 RELEASE_NOTES.md        %{buildroot}/%{_docsdir}
install -m 444 DISCLAIMER              %{buildroot}/%{_docsdir}

install -D -m755 contribs/sjstat %{buildroot}/%{_bindir}/sjstat

make install DESTDIR=%{buildroot}
make install-contrib DESTDIR=%{buildroot}

install -D -m644 etc/sackd.service %{buildroot}/%{_unitdir}/sackd.service
install -D -m644 etc/slurmd.service %{buildroot}%{_unitdir}/slurmd.service
install -D -m644 etc/slurmctld.service %{buildroot}%{_unitdir}/slurmctld.service
install -D -m644 etc/slurmdbd.service %{buildroot}%{_unitdir}/slurmdbd.service
install -D -m644 cm-slurmrestd.service %{buildroot}%{_unitdir}/slurmrestd.service
install -D -m644 cm-slurmrestd.sysconfig %{buildroot}%{_sysconfigdir}/slurmrestd

%if %{sles15}
  echo "LD_LIBRARY_PATH=/cm/local/apps/http-parser/lib:\$LD_LIBRARY_PATH" >> %{buildroot}%{_sysconfigdir}/slurmrestd
%endif

ln -s %{major_slurm_version} %{buildroot}/%{_current_link}

# Delete unpackaged files:
find %{buildroot} -name '*.a' -exec rm {} \;
find %{buildroot} -name '*.la' -exec rm {} \;
rm -f %{buildroot}/%{_libdir}/slurm/job_submit_defaults.so
rm -f %{buildroot}/%{_libdir}/slurm/job_submit_logging.so
rm -f %{buildroot}/%{_libdir}/slurm/job_submit_partition.so
rm -f %{buildroot}/%{_libdir}/slurm/auth_none.so
rm -f %{buildroot}/%{_libdir}/slurm/cred_none.so
rm -f %{buildroot}/%{_sbindir}/sfree
rm -f %{buildroot}/%{_sbindir}/slurm_epilog
rm -f %{buildroot}/%{_sbindir}/slurm_prolog
rm -f %{buildroot}/%{_sysconfdir}/init.d/slurm
rm -f %{buildroot}/%{_sysconfdir}/init.d/slurmdbd
rm -f %{buildroot}/%{_perldir}/auto/Slurm/.packlist
rm -f %{buildroot}/%{_perldir}/auto/Slurm/Slurm.bs
rm -f %{buildroot}/%{_perlarchlibdir}/perllocal.pod
rm -f %{buildroot}/%{_perldir}/perllocal.pod
rm -f %{buildroot}/%{_perldir}/auto/Slurmdb/.packlist
rm -f %{buildroot}/%{_perldir}/auto/Slurmdb/Slurmdb.bs

# Build man pages that are generated directly by the tools
rm -f %{buildroot}/%{_mandir}/man1/sjobexitmod.1
%{buildroot}%{_bindir}/sjobexitmod --roff > %{buildroot}/%{_mandir}/man1/sjobexitmod.1
rm -f %{buildroot}/%{_mandir}/man1/sjstat.1
%{buildroot}%{_bindir}/sjstat --roff > %{buildroot}/%{_mandir}/man1/sjstat.1

# Prepare pam files
LIST=./pam.files
touch $LIST
test -f %{buildroot}/lib/security/pam_slurm.so && echo /lib/security/pam_slurm.so   >>$LIST
test -f %{buildroot}/lib32/security/pam_slurm.so && echo /lib32/security/pam_slurm.so >>$LIST
test -f %{buildroot}/lib64/security/pam_slurm.so && echo /lib64/security/pam_slurm.so >>$LIST
test -f %{buildroot}/lib/security/pam_slurm_adopt.so && echo /lib/security/pam_slurm_adopt.so   >>$LIST
test -f %{buildroot}/lib32/security/pam_slurm_adopt.so && echo /lib32/security/pam_slurm_adopt.so   >>$LIST
test -f %{buildroot}/lib64/security/pam_slurm_adopt.so && echo /lib64/security/pam_slurm_adopt.so   >>$LIST

### Pyxis and Enroot files
chmod +x ./install-pyxis.sh
install -m 700 install-pyxis.sh             %{buildroot}/%{_scriptsdir}
install -m 644 prolog-enroot.sh.jinja2      %{buildroot}/%{_templatesdir}
install -m 644 epilog-enroot.sh.jinja2      %{buildroot}/%{_templatesdir}
install -m 644 enroot.conf.jinja2           %{buildroot}/%{_templatesdir}
install -m 644 enroot-sysctl.conf.template  %{buildroot}/%{_templatesdir}
install -m 644 pyxis.conf.template          %{buildroot}/%{_templatesdir}

# Strip out dependencies
cat > %{buildroot}/find-requires.sh <<EOF
exec %{__find_requires} "$@" | egrep -v '^libpmix.so|libnvidia-ml|libhdf|libevent|libhwloc.so'
EOF
chmod +x %{buildroot}/find-requires.sh
%global _use_internal_dependency_generator 0
%global __find_requires %{buildroot}/find-requires.sh
#############################################################################

%clean
rm -rf %{buildroot}
#############################################################################

%files
%defattr(-,root,root,0755)

### BCM files and directories
%{_templatesdir}
%{_scriptsdir}
%{_epilogsdir}
%{_prologsdir}
%{_spooldir}
%{_current_link}
%attr(0700,root,root) %{_templatesdir}/prolog-enroot.sh.jinja2
%attr(0700,root,root) %{_templatesdir}/epilog-enroot.sh.jinja2
%config(noreplace) %attr(0600,slurm,slurm) %{_templatesdir}/slurmdbd.conf.template

### Slurm common files
%{_cmdir}
%{_docsdir}
%{_bindir}/s*
%exclude %{_bindir}/seff
%exclude %{_bindir}/sjobexitmod
%exclude %{_bindir}/sjstat
%exclude %{_bindir}/smail
%{_libdir}/*.so*
%exclude %{_libdir}/slurm/select_gnl_cons_tres.so
%{_libdir}/slurm/src/*
%{_libdir}/slurm/*.so
%exclude %{_libdir}/slurm/accounting_storage_mysql.so
%exclude %{_libdir}/slurm/job_submit_pbs.so
%exclude %{_libdir}/slurm/spank_pbs.so
%{_mandir}
%exclude %{_mandir}/man1/sjobexit*
%exclude %{_mandir}/man1/sjstat*
%dir %{_libdir}/slurm/src
#############################################################################

%if %{use_prs}
%files prs
%{_libdir}/slurm/select_gnl_cons_tres.so
%endif

#############################################################################

%files devel
%defattr(-,root,root)
%dir %attr(0755,root,root)
%dir %{_prefix}/include/slurm
%{_prefix}/include/slurm/*
%dir %{_libdir}/pkgconfig
%{_libdir}/pkgconfig/slurm.pc
#############################################################################

%files perlapi
%defattr(-,root,root)
%{_perldir}/Slurm.pm
%{_perldir}/Slurm/Bitstr.pm
%{_perldir}/Slurm/Constant.pm
%{_perldir}/Slurm/Hostlist.pm
%{_perldir}/auto/Slurm/Slurm.so
%{_perldir}/Slurmdb.pm
%{_perldir}/auto/Slurmdb/Slurmdb.so
%{_perldir}/auto/Slurmdb/autosplit.ix
%{_perlman3dir}/Slurm*
#############################################################################

%files slurmctld
%defattr(-,root,root)
%{_sbindir}/slurmctld
%{_unitdir}/slurmctld.service
%config (noreplace) /etc/logrotate.d/slurmctld
#############################################################################

%files slurmd
%defattr(-,root,root)
%{_sbindir}/slurmd
%{_sbindir}/slurmstepd
%{_unitdir}/slurmd.service
%config (noreplace) /etc/logrotate.d/slurmd
%{_vardir}
#############################################################################

%files slurmdbd
%defattr(-,root,root)
%{_sbindir}/slurmdbd
%{_libdir}/slurm/accounting_storage_mysql.so

%config (noreplace) /etc/logrotate.d/slurmdbd
%{_unitdir}/slurmdbd.service
#############################################################################

%files libpmi
%defattr(-,root,root)
%{_libdir}/libpmi*
#############################################################################

%files torque
%defattr(-,root,root)
%{_bindir}/pbsnodes
%{_bindir}/qdel
%{_bindir}/qhold
%{_bindir}/qrls
%{_bindir}/qstat
%{_bindir}/qsub
%{_bindir}/qalter
%{_bindir}/qrerun
%{_bindir}/mpiexec
%{_bindir}/generate_pbs_nodefile
%{_libdir}/slurm/job_submit_pbs.so
%{_libdir}/slurm/spank_pbs.so
#############################################################################

%files openlava
%defattr(-,root,root)
%{_bindir}/bjobs
%{_bindir}/bkill
%{_bindir}/bsub
%{_bindir}/lsid
#############################################################################

%files contribs
%defattr(-,root,root)
%{_bindir}/seff
%{_bindir}/sjobexitmod
%{_bindir}/sjstat
%{_bindir}/smail
%{_mandir}/man1/sjstat*
#############################################################################

%files -f pam.files pam
%defattr(-,root,root)
#############################################################################

%files slurmrestd
%{_sbindir}/slurmrestd
%attr(0700,root,root) %{_scriptsdir}/cm-slurmrestd-setup
%config (noreplace) %{_sysconfigdir}/slurmrestd
%{_unitdir}/slurmrestd.service
#############################################################################

%files sackd
%defattr(-,root,root)
%{_sbindir}/sackd
%{_unitdir}/sackd.service
#############################################################################

%post

###### SLURMDBD PASSWORD
# If slurmdbd will use the head node's DB, it needs to know what password to use, since
# it is setup during installation. Given that slurm is not setup when BCM is deployed, the
# slurmdbd password is saved in the slurmdbd.conf.template file.
#
# This also means that during installation of slurm packages, the _new_ template files
# have to get the password from preexisting template files.

function get_previous_password {
  ls -1 --reverse /cm/local/apps/slurm/ | egrep -v "current|var" | while read slurm_version; do
    if [ -f /cm/local/apps/slurm/${slurm_version}/templates/slurmdbd.conf.template ]; then
      other_template=/cm/local/apps/slurm/${slurm_version}/templates/slurmdbd.conf.template
    elif [ -f /cm/local/apps/slurm/${slurm_version}/templates/slurmdbd.conf.template.rpmsave ]; then
      other_template=/cm/local/apps/slurm/${slurm_version}/templates/slurmdbd.conf.template.rpmsave
    fi
    if [ -z "${other_template}" ]; then
      continue
    fi
    if ! grep '^StoragePass=STORAGE_PASSWD$' ${other_template} > /dev/null 2>&1; then
      grep '^StoragePass=' ${other_template} | sed 's/^StoragePass=//' -
      break
    fi
  done
}

function adjust_password {
  grep '^StoragePass=STORAGE_PASSWD$' $1 > /dev/null 2>&1 || return 0
  passwd=$( get_previous_password )
  if [ -n "$passwd" ]; then
    echo Will adjust storage password for slurmdbd.conf.template file
    escaped_passwd=$(printf '%s\n' "${passwd}" | sed 's/[&/\]/\\&/g')
    sed -i "s/^StoragePass=.*/StoragePass=${escaped_passwd}/" "$1"
  fi
}

TEMPLATE=/cm/local/apps/slurm/current/templates/slurmdbd.conf.template
if [ -e $TEMPLATE ]; then
  adjust_password $TEMPLATE
else
  echo "No such file to adjust slurmdbd password: $TEMPLATE"
fi

####### END OF SLURMDBD PASSWORD

/sbin/ldconfig

%postun
/sbin/ldconfig

#############################################################################

%post slurmd
chown -R slurm:slurm %{_spooldir} 2>/dev/null
if [ ! -d /var/run/slurm ]; then
  mkdir -p /var/run/slurm
  chown -R slurm:slurm /var/run/slurm
fi

# precreate log file due to Slurm bug: https://bugs.schedmd.com/show_bug.cgi?id=18727
touch /var/log/slurmd 2>/dev/null
chown slurm:slurm /var/log/slurmd 2>/dev/null

%systemd_post slurmd.service

%preun slurmd
%systemd_preun slurmd.service

%postun slurmd
%systemd_postun_with_restart slurmd.service
#############################################################################

%post slurmdbd

# precreate log file due to Slurm bug: https://bugs.schedmd.com/show_bug.cgi?id=18727
touch /var/log/slurmdbd 2>/dev/null
chown slurm:slurm /var/log/slurmdbd 2>/dev/null

%systemd_post slurmdbd.service

%preun slurmdbd
%systemd_preun slurmdbd.service

%postun slurmdbd
%systemd_postun_with_restart slurmdbd.service
#############################################################################

%post slurmctld

# precreate log file due to Slurm bug: https://bugs.schedmd.com/show_bug.cgi?id=18727
touch /var/log/slurmctld 2>/dev/null
chown slurm:slurm /var/log/slurmctld 2>/dev/null

%systemd_post slurmctld.service

%preun slurmctld
%systemd_preun slurmctld.service

%postun slurmctld
%systemd_postun_with_restart slurmctld.service
#############################################################################

%post slurmrestd
%systemd_post slurmrestd.service

%preun slurmrestd
%systemd_preun slurmrestd.service

%postun slurmrestd
%systemd_postun_with_restart slurmrestd.service
#############################################################################

%post sackd
%systemd_post sackd.service

%preun sackd
%systemd_preun sackd.service

%postun sackd
%systemd_postun_with_restart sackd.service
