%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           argo-atp
Version:        1.0.0
Release:        3%{?dist}
Summary:        The Aggregated Topology Provider (ATP) contains grid topology information.
Group:          Development/Languages
License:        ASL 2.0
URL:            http://tomtools.cern.ch/confluence/display/SAMDOC
Source0:        argo-atp-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
Requires:       MySQL-python
Requires:       PyYAML >= 3.08
Requires:       libyaml >= 0.1.2
Requires:       mx >= 2.0.6
Requires:       python-django-pagination
Requires:       python-ldap >= 2.2.0
Requires:       python-lxml
Requires:       python-simplejson >= 2.0.3
Requires:       python-uuid
Requires:       stomppy
Conflicts:      atp

%define stripargo() %(echo %1 | sed 's/argo-//')

%description
The Aggregated Topology Provider (ATP) is a database containing grid 
topology information. This means list of projects (like WLCG), grid 
infrastructures (EGEE, OSG, NDGF), sites, services, VOs and their 
groupings, downtimes and a history of these.

%prep
%setup -q

%build
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
python setup.py install --root=$RPM_BUILD_ROOT

install -d -m 755 $RPM_BUILD_ROOT/var/log/%{stripargo %{name}}/

%clean
rm -rf $RPM_BUILD_ROOT

%pre
# Create nagios user
if ! /usr/bin/id nagios &>/dev/null; then
    /usr/sbin/useradd -r -m -d /var/log/nagios -s /bin/sh -c "nagios" nagios || \
        logger -t nagios/rpm "Unexpected error adding user \"nagios\". Aborting installation."
fi
if ! /usr/bin/getent group nagiocmd &>/dev/null; then
    /usr/sbin/groupadd nagiocmd &>/dev/null || \
        logger -t nagios/rpm "Unexpected error adding group \"nagiocmd\". Aborting installation."
fi

# All the DB schema files & synchronizer
%files
%defattr(-,root,root,-)
%{_bindir}/atp_synchro
%{_bindir}/check_atp_sync
%{_bindir}/atp-createdb
%{python_sitelib}/atp_synchronizer/*
%{python_sitelib}/mywlcg-atp-api/*
%{python_sitelib}/atp/*
%{python_sitelib}/*egg-info
%doc README LICENSE mysql_schema CHANGES
%config(noreplace) %{_sysconfdir}/%{stripargo %{name}}/atp_vo_feeds_schema.xsd
%config(noreplace) %{_sysconfdir}/%{stripargo %{name}}/atp_synchro.conf
%config(noreplace) %{_sysconfdir}/%{stripargo %{name}}/vo_feeds.conf
%config(noreplace) %{_sysconfdir}/%{stripargo %{name}}/roc.conf
%config(noreplace) %{_sysconfdir}/%{stripargo %{name}}/atp_logging_files.conf
%config(noreplace) %{_sysconfdir}/%{stripargo %{name}}/atp_logging_parameters_config.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/atp.logrotate
%config(noreplace) %attr(0640,root,nagios) %{_sysconfdir}/%{stripargo %{name}}/atp_db.conf
%dir %{_var}/log/%{stripargo %{name}}
%attr(0644,root,root) %{_sysconfdir}/cron.d/atp-sync
%attr(0755,root,root) %{_sysconfdir}/init.d/atp-sync
%{_sysconfdir}/%{stripargo %{name}}_django/requires.txt
%{_sysconfdir}/%{stripargo %{name}}_django/atp*
%{_datadir}/%{stripargo %{name}}/apache/atp-pi.wsgi
%{_datadir}/%{stripargo %{name}}/manage
%config(noreplace) /etc/httpd/conf.d/xatp-pi.conf

%changelog
* Fri Dec 25 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.0.0-3{?dist}
- cron script fix
* Mon May 11 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.0.0-2{?dist}
- remove obsoleted info
- configuration update
- package dependencies updated
* Thu Jan 29 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.0.0-1{?dist}
- ATP for ARGO transition period
