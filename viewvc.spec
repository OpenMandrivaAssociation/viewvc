Name:           viewvc
Version:        1.1.15
Release:        5
Epoch:          0
Summary:        Browser interface for CVS and Subversion version control repositories
License:        BSD
Group:          System/Servers
URL:            http://www.viewvc.org/
Source0:        http://viewvc.tigris.org/files/documents/3330/48659/%name-%version.tar.gz
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
%{__python} -O %{_libdir}/python%{py_ver}/compileall.py %{buildroot}%{_datadir}/%{name}/lib

# apache configuration
%{__mkdir_p} %{buildroot}%{_webappconfdir}
%{__cat} > %{buildroot}%{_webappconfdir}/%{name}.conf <<EOF
# %{name} configuration

Alias /%{name} %{_var}/www/%{name}

<Directory %{_var}/www/%{name}>
    Require all granted
</Directory>

<LocationMatch "^/cgi-bin/(query|viewvc).cgi">
    Require local granted
    ErrorDocument 403 "Access denied per %{_sysconfdir}/httpd/conf/webapps.d/%{name}.conf"
</LocationMatch>

<IfModule mod_python.c>
    Alias /%{name}-mp %{_datadir}/%{name}/bin/mod_python/viewvc.py
    <Directory %{_datadir}/%{name}/bin/mod_python>
        AddHandler python-program .py
        PythonHandler handler
        Require local granted
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

%files
%doc CHANGES COMMITTERS INSTALL LICENSE.html README README.mdv docs/
%config(noreplace) %{_sysconfdir}/%{name}
%config(noreplace) %{_webappconfdir}/%{name}.conf
%{_datadir}/%{name}
%{_var}/www/cgi-bin/*.cgi
%{_var}/www/%{name}


%changelog
* Tue Jun 26 2012 Oden Eriksson <oeriksson@mandriva.com> 0:1.1.15-1mdv2012.0
+ Revision: 806951
- a python rpm macro vanished...
- 1.1.15

* Tue May 17 2011 Funda Wang <fwang@mandriva.org> 0:1.1.11-1
+ Revision: 675885
- new version 1.1.11

* Wed Mar 02 2011 Juan Luis Baptiste <juancho@mandriva.org> 0:1.1.9-1
+ Revision: 641297
- Updated to 1.1.9

  + Michael Scherer <misc@mandriva.org>
    - update to 1.1.8

* Fri Sep 10 2010 Funda Wang <fwang@mandriva.org> 0:1.1.7-1mdv2011.0
+ Revision: 577118
- new version 1.1.7

* Tue Mar 30 2010 Oden Eriksson <oeriksson@mandriva.com> 0:1.1.5-1mdv2010.1
+ Revision: 528953
- 1.1.5

* Thu Mar 11 2010 Oden Eriksson <oeriksson@mandriva.com> 0:1.1.4-1mdv2010.1
+ Revision: 517984
- 1.1.4

* Sun Jan 17 2010 Guillaume Rousse <guillomovitch@mandriva.org> 0:1.1.3-3mdv2010.1
+ Revision: 492703
- use herein document instead of external source for README.mdv
- rely on filetrigger for reloading apache configuration begining with 2010.1, rpm-helper macros otherwise

* Thu Jan 07 2010 Oden Eriksson <oeriksson@mandriva.com> 0:1.1.3-2mdv2010.1
+ Revision: 487113
- added mod_python support
- whoops, really fix path to templates
- limit access to the cgi files per default
- more config fixes
- package mod_python files
- fix path to templates

* Wed Dec 30 2009 Frederik Himpe <fhimpe@mandriva.org> 0:1.1.3-1mdv2010.1
+ Revision: 484041
- Update to new version 1.1.3

* Wed Aug 12 2009 Funda Wang <fwang@mandriva.org> 0:1.1.2-1mdv2010.0
+ Revision: 415260
- new version 1.1.2

* Fri Jun 05 2009 Funda Wang <fwang@mandriva.org> 0:1.1.1-1mdv2010.0
+ Revision: 383002
- update tools patch
- New version 1.1.1

* Sun Nov 30 2008 David Walluck <walluck@mandriva.org> 0:1.1.0-0.beta1.1mdv2009.1
+ Revision: 308328
- 1.1.0

* Sat Oct 18 2008 David Walluck <walluck@mandriva.org> 0:1.0.7-1mdv2009.1
+ Revision: 295155
- remove obsolete patches
- 1.0.7

* Thu Sep 18 2008 Frederik Himpe <fhimpe@mandriva.org> 0:1.0.5-5mdv2009.0
+ Revision: 285705
- Add patch from upstream svn fixing a small security problem
  (http://viewvc.tigris.org/issues/show_bug.cgi?id=354)

* Sun Aug 03 2008 Thierry Vignaud <tv@mandriva.org> 0:1.0.5-4mdv2009.0
+ Revision: 261852
- rebuild

* Wed Jul 30 2008 Thierry Vignaud <tv@mandriva.org> 0:1.0.5-3mdv2009.0
+ Revision: 255528
- rebuild

* Tue Mar 04 2008 Frederik Himpe <fhimpe@mandriva.org> 0:1.0.5-1mdv2008.1
+ Revision: 178842
- New upstream bug and security fix release

  + Olivier Blin <blino@mandriva.org>
    - restore BuildRoot

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request

* Wed Aug 22 2007 Guillaume Rousse <guillomovitch@mandriva.org> 0:1.0.4-3mdv2008.0
+ Revision: 69124
- requires python, for cgi module

* Fri Jun 01 2007 David Walluck <walluck@mandriva.org> 0:1.0.4-2mdv2008.0
+ Revision: 33680
- version explicit Obsoletes
- fix patch specifying config file location
- remove epoch from the build root
- update README.mdv a bit

* Tue Apr 17 2007 David Walluck <walluck@mandriva.org> 0:1.0.4-1mdv2008.0
+ Revision: 14167
- 1.0.4

