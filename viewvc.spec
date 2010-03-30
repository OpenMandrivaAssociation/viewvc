Name:           viewvc
Version:        1.1.5
Release:        %mkrel 1
Epoch:          0
Summary:        Browser interface for CVS and Subversion version control repositories
License:        BSD
Group:          System/Servers
URL:            http://www.viewvc.org/
Source0:        http://viewvc.tigris.org/files/documents/3330/46029/%name-%version.tar.gz
Patch0:         %{name}-tools.patch
Patch1:         %{name}-1.1.0-config.patch
Requires:       apache
Requires(post): rpm-helper
Requires(postun): rpm-helper
BuildRequires:  python
Requires:       python
Obsoletes:      viewcvs < %{epoch}:%{version}-%{release}
Provides:       viewcvs = %{epoch}:%{version}-%{release}
BuildArch:      noarch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root

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
%setup -q -n %{name}-%{version}
%patch0 -p1
%patch1 -p0 -b .config

%build

%install
%{__rm} -rf %{buildroot}
%{__python} ./viewvc-install --destdir=%{buildroot} --prefix=%{_datadir}/%{name}

# remove uneeded files
%{__rm} -f %{buildroot}%{_datadir}/%{name}/bin/mod_python/.htaccess

# fix python files perms and shellbang
%{__perl} -pi \
        -e 's|/usr/local/bin/python|%{_bindir}/python|g;' \
        -e 's|\s*/usr/bin/env python|%{_bindir}/python|g;' \
        -e 's|CONF_PATHNAME =.*|CONF_PATHNAME = r"%{_sysconfdir}/%{name}/viewvc.conf"|g;' \
        `%{_bindir}/find %{buildroot}%{_datadir}/%{name} -type f` 

# install cgi's to www directory
%{__mkdir_p} %{buildroot}%{_var}/www/cgi-bin
%{__install} -m 755 %{buildroot}%{_datadir}/%{name}/bin/cgi/*.cgi %{buildroot}%{_var}/www/cgi-bin
%{__rm} -rf %{buildroot}%{_datadir}/%{name}/bin/cgi

# fix paths in configuration
%{__perl} -pi \
  -e 's|^#template_dir = .*|template_dir = %{_datadir}/%{name}/templates/|g;' \
  -e 's|^#docroot = .*|docroot = /%{name}|;' \
  -e 's|^#cvsgraph_conf = .*|cvsgraph_conf = %{_sysconfdir}/%{name}/cvsgraph.conf|;' \
  -e 's|^#mime_types_files = .*|mime_types_files = %{_sysconfdir}/%{name}/mimetypes.conf, %{_sysconfdir}/httpd/conf/mime.types|;' \
  %{buildroot}%{_datadir}/%{name}/viewvc.conf

# install config to sysconf directory
%{__mkdir_p} %{buildroot}%{_sysconfdir}/%{name}
%{__install} -m 644 %{buildroot}%{_datadir}/%{name}/viewvc.conf %{buildroot}%{_sysconfdir}/%{name}/viewvc.conf
%{__rm} -f %{buildroot}%{_datadir}/%{name}/viewvc.conf
%{__install} -m 644 %{buildroot}%{_datadir}/%{name}/cvsgraph.conf %{buildroot}%{_sysconfdir}/%{name}/cvsgraph.conf
%{__rm} -f %{buildroot}%{_datadir}/%{name}/cvsgraph.conf
%{__install} -m 644 %{buildroot}%{_datadir}/%{name}/mimetypes.conf %{buildroot}%{_sysconfdir}/%{name}/mimetypes.conf
%{__rm} -f %{buildroot}%{_datadir}/%{name}/mimetypes.conf

# move static files under %{_var}/www
%{__mv} %{buildroot}%{_datadir}/%{name}/templates/docroot %{buildroot}%{_var}/www/%{name}

# compile the python files
%{_bindir}/find %{buildroot}%{_datadir}/%{name}/lib -type f -name "*.pyc" | %{_bindir}/xargs %{__rm}
%{__python} -O %{_libdir}/python%{pyver}/compileall.py %{buildroot}%{_datadir}/%{name}/lib

# apache configuration
%{__mkdir_p} %{buildroot}%{_webappconfdir}
%{__cat} > %{buildroot}%{_webappconfdir}/%{name}.conf <<EOF
# %{name} configuration

Alias /%{name} %{_var}/www/%{name}

<Directory %{_var}/www/%{name}>
    Allow from all
</Directory>

<LocationMatch "^/cgi-bin/(query|viewvc).cgi">
    Order deny,allow
    Deny from all
    Allow from 127.0.0.1
    ErrorDocument 403 "Access denied per %{_sysconfdir}/httpd/conf/webapps.d/%{name}.conf"
</LocationMatch>

<IfModule mod_python.c>
    Alias /%{name}-mp %{_datadir}/%{name}/bin/mod_python/viewvc.py
    <Directory %{_datadir}/%{name}/bin/mod_python>
        AddHandler python-program .py
        PythonHandler handler
        Order allow,deny
        Allow from 127.0.0.1
        ErrorDocument 403 "Access denied per %{_sysconfdir}/httpd/conf/webapps.d/%{name}.conf"
    </Directory>
</IfModule>
EOF

# set mode 755 on executable scripts
%{__grep} -rl '^#!' %{buildroot}%{_datadir}/%{name} | %{_bindir}/xargs %{__chmod} 755

cat >README.mdv <<EOF
Mandriva RPM specific notes
===========================

Setup
-----
The setup used here differs from default one in order to achieve better FHS
compliance:

- the files accessible from the web are in /var/www/cgi-bin
- the files not accessible from the web are in /usr/share/viewvc
- the configuration file is located at /etc/viewvc/viewvc.conf

Post-installation
-----------------
You have manually to create the MySQL database if you want to use query mode.

Additional useful packages
--------------------------
- cvs and rcs provide a web interface for CVS repositories
- python-svn provides a web interface for SVN repositories
- MySQL-python and a MySQL database are needed for query mode
- apache-mod_python, will be accessible at http://localhost/viewvc-mp (instead
  of the cgi files)
EOF

%clean
%{__rm} -rf %{buildroot}

%post
%if %mdkversion < 201010
%_post_webapp
%endif

%postun
%if %mdkversion < 201010
%_postun_webapp
%endif

%files
%defattr(-,root,root)
%doc CHANGES COMMITTERS INSTALL LICENSE.html README README.mdv docs/
%config(noreplace) %{_sysconfdir}/%{name}
%config(noreplace) %{_webappconfdir}/%{name}.conf
%{_datadir}/%{name}
%{_var}/www/cgi-bin/*.cgi
%{_var}/www/%{name}
