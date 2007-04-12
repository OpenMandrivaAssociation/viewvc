%define name		viewvc
%define version		1.0.3
%define date		2006-04-10
%define stable		1
%if !%{stable}
%define snapshot	20060410
%define release		%mkrel 2
%else
%define release		%mkrel 2
%endif

Name:		%{name}
Version:	%{version}
Release:	%{release}
Summary:	A browser interface for CVS and Subversion version control repositories
Epoch:		0
License:	BSD
Group:		System/Servers
%if !%{stable}
Source0:	http://www.viewvc.org/nightly/%{name}-%{date}.tar.bz2
%else
Source0:	http://www.viewvc.org/viewvc-%{version}.tar.bz2
%endif
Source1:	%{name}.README.mdv
Patch0:		%{name}-tools.patch
Patch1:		%{name}-1.0.config.patch
# speed up directory listing when paging (from trunk r1504)
Patch2:		%{name}-r1504-view_directory_cheating.patch
URL:		http://www.viewvc.org/
Requires:	apache
# webapp macros and scriptlets
Requires(post): rpm-helper >= 0.16-2mdv2007.0
Requires(postun): rpm-helper >= 0.16-2mdv2007.0
BuildRequires:	rpm-helper >= 0.16-2mdv2007.0
BuildRequires:	rpm-mandriva-setup >= 1.23-1mdv2007.0
BuildRequires:  python
BuildArch:	noarch
BuildRoot:	%{_tmppath}/%{name}-%{version}
Obsoletes:	viewcvs
Provides:	viewcvs = %{epoch}:%{version}-%{release}

%description
ViewVC is a browser interface for CVS and Subversion version control 
repositories. It generates templatized HTML to present navigable 
directory, revision, and change log listings. It can display specific 
versions of files as well as diffs between those versions. Basically, 
ViewVC provides the bulk of the report-like functionality you expect out 
of your version control tool, but much more prettily than the average 
textual command-line program output.

Here are some of the additional features of ViewVC:

    * Support for filesystem-accessible CVS and Subversion repositories.
    * Individually configurable virtual host support.
    * Line-based annotation/blame display (CVS only).
    * Revision graph capabilities (via integration with CvsGraph) (CVS 
      only).
    * Syntax highlighting support (via integration with GNU enscript).
    * Bonsai-like repository query facilities.
    * Template-driven output generation.
    * Colorized, side-by-side differences.
    * Tarball generation (by tag/branch for CVS, by revision for 
      Subversion).
    * I18N support based on the Accept-Language request header.
    * Ability to run either as CGI script or as a standalone server.
    * Regexp-based file searching.
    * INI-like configuration file (as opposed to requiring actual code 
      tweaks).

%prep
%if !%{stable}
%setup -q -n %{name}-%{date}
%else
%setup -q
%endif
%patch0 -p1
%patch1 -p0
%patch2 -p0
%{__cp} -a %{SOURCE1} README.mdv
find . -type d -name .svn | xargs %{__rm} -rf

%build

%install
%{__rm} -rf %{buildroot}
%{__python} ./viewvc-install --destdir=%{buildroot} --prefix=%{_datadir}/%{name}

# remove mod_python files
%{__rm} -rf %{buildroot}%{_datadir}/%{name}/bin/mod_python

# fix python files perms and shellbang
%{__perl} -pi \
	-e 's|/usr/local/bin/python|%{_bindir}/python|g;' \
	-e 's|\s*/usr/bin/env python|%{_bindir}/python|g;' \
	-e 's|CONF_PATHNAME =.*|CONF_PATHNAME = r"%{_sysconfdir}/%{name}/viewvc.conf"|g;' \
	`find %{buildroot}%{_datadir}/%{name} -type f` 

# install cgi's to www directory
%{__mkdir_p} %{buildroot}%{_var}/www/cgi-bin
%{__install} -m 755 %{buildroot}%{_datadir}/%{name}/bin/cgi/*.cgi %{buildroot}%{_var}/www/cgi-bin
%{__rm} -rf %{buildroot}%{_datadir}/%{name}/bin/cgi

# fix paths in configuration
%{__perl} -pi \
  -e 's|templates/|%{_datadir}/%{name}/templates/|g;' \
  -e 's|^#docroot = .*|docroot = /%{name}|;' \
  -e 's|^cvsgraph_conf = .*|cvsgraph_conf = %{_sysconfdir}/%{name}/cvsgraph.conf|;' \
  %{buildroot}%{_datadir}/%{name}/viewvc.conf

# install config to sysconf directory
%{__mkdir_p} %{buildroot}%{_sysconfdir}/%{name}
%{__install} -m 644 %{buildroot}%{_datadir}/%{name}/viewvc.conf %{buildroot}%{_sysconfdir}/%{name}/viewvc.conf
%{__rm} -f %{buildroot}%{_datadir}/%{name}/viewvc.conf
%{__install} -m 644 %{buildroot}%{_datadir}/%{name}/cvsgraph.conf %{buildroot}%{_sysconfdir}/%{name}/cvsgraph.conf
%{__rm} -f %{buildroot}%{_datadir}/%{name}/cvsgraph.conf

# move static files under %{_var}/www
%{__mv} %{buildroot}%{_datadir}/%{name}/templates/docroot %{buildroot}%{_var}/www/%{name}

# compile the python files
find %{buildroot}%{_datadir}/%{name}/lib -type f -name "*.pyc" | xargs %{__rm} -f
%{__python} -O %{_libdir}/python%{pyver}/compileall.py \
%{buildroot}%{_datadir}/%{name}/lib

# apache configuration
%{__mkdir_p} %{buildroot}%{_webappconfdir}
%{__cat} > %{buildroot}%{_webappconfdir}/%{name}.conf <<EOF
# %{name} configuration

Alias /%{name} %{_var}/www/%{name}

<Directory %{_var}/www/%{name}>
    Allow from all
</Directory>
EOF

# set mode 755 on executable scripts
%{__grep} -rl '^#!' %{buildroot}%{_datadir}/%{name} | xargs %{__chmod} 755

%clean
%{__rm} -rf %{buildroot}

%post
%{_post_webapp}

%postun
%{_postun_webapp}

%files
%defattr(-,root,root)
%doc CHANGES README INSTALL TODO README.mdv
%config(noreplace) %{_sysconfdir}/%{name}
%config(noreplace) %{_webappconfdir}/%{name}.conf
%{_datadir}/%{name}
%{_var}/www/cgi-bin/*.cgi
%{_var}/www/%{name}


