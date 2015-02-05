#!/usr/bin/perl -w
# 
###################################
#
# NAME:		deploy_dbschema.pl
#
# DATE:		February - 2013
#
###################################
# 
use strict;
use File::Temp qw/ tempfile /;
use Getopt::Long;

# Get parameters
my $params = {};
GetOptions($params,
  'db_user:s',
  'db_name:s',
  'db_pass:s',
  'db_type:s',
);

# Check parameters
unless ( defined $params->{db_user}
       ) {
    print STDERR "ERROR: No db_user parameter given\n";
    exit 0;
}
unless ( defined $params->{db_name}
       ) {
    print STDERR "ERROR: No db_name parameter given\n";
    exit 0;
}
unless ( defined $params->{db_pass}
       ) {
    print STDERR "ERROR: No db_pass parameter given\n";
    exit 0;
}
unless ( defined $params->{db_type}
       ) {
    print STDERR "ERROR: No db_type parameter given\n";
    exit 0;
}

my $db_user=$params->{db_user};
my $db_name=$params->{db_name};
my $db_pass=$params->{db_pass};
my $db_type=$params->{db_type};

if (!$db_user || !$db_name || !$db_pass) {
  print STDERR "Missing DB connection information\n";
  exit 1;
}

sub run_db_script($) {
  my ($script) = @_;
  my ($fail,$empty)=(0,0);
  my ($tfh, $tfname) = tempfile(UNLINK => 1);
  local(*CMD);

  my $dir = $script;
  $dir =~ s/\/[^\/]*$//;
  
  if ($db_type eq "oracle")
  {
	  if  (open(CMD, "| ( cd $dir; sqlplus -S -L /nolog >".$tfname." )")) {
	  	print CMD "whenever sqlerror exit sql.sqlcode\n";
	  	print CMD "whenever oserror exit sql.oscode\n";
	  	print CMD "CONN ".$db_user."/".$db_pass."\@".$db_name."\n";
	  	print CMD "set head off\n";
	  	print CMD "set feed off\n";
	  	print CMD "\@ $script\n";
	  	print CMD "quit\n";
	  	close(CMD);
	  	$fail++ if $?;
	  } else {
	  	$fail++;
	  }
  }
  elsif ($db_type eq "mysql")
  {
  	if  (open(CMD, "| ( cd $dir; mysql -u $db_user --password=${db_pass} >".$tfname." )")) {
		print CMD "use $db_name\n";
    	print CMD "source $script\n";
    	print CMD "quit\n";
    	close(CMD);
    	$fail++ if $?;
  	} else {
    	$fail++;
  	}
  }
  
  close $tfh;
  if ($fail) {
  	system("cat $tfname 1>&2");
  	return undef;
  }
  return 1;
}

sub get_details($) {
  my ($hash_ref) = @_;
  my ($fail,$empty)=(0,0);
  my ($tfh, $tfname) = tempfile(UNLINK => 1);
  local(*CMD);
  if ($db_type eq "oracle")
  {
	  if  (open(CMD, "| sqlplus -S -L /nolog >".$tfname)) {
	  	print CMD "whenever sqlerror exit sql.sqlcode\n";
	  	print CMD "whenever oserror exit sql.oscode\n";
	  	print CMD "CONN ".$db_user."/".$db_pass."\@".$db_name."\n";
	  	print CMD "set head off\n";
	  	print CMD "select ver,db_name from schema_details;\n";
	  	print CMD "quit\n";
	  	close(CMD);
	  	my $ret = $?;
	  	if (($ret & 192)==0 && ($ret>>8)==174) {
	 	   $empty = 1;
	  	} elsif ($ret) {
	  	  $fail++;
	  	}
	  } else {
	  	$fail++;
	  }
  }
  elsif ($db_type eq "mysql")
  {
	  if  (open(CMD, "| mysql -u $db_user --password=${db_pass} >".$tfname)) {
		print CMD "use $db_name\n";
	  	print CMD "select ver,db_name from schema_details;\n";
	  	print CMD "quit\n";
	  	close(CMD);
	  	my $ret = $?;
	  	if (($ret & 192)==0 && ($ret>>8)==174) {
	 	   $empty = 1;
	  	} elsif ($ret) {
	  	  $fail++;
	  	}
	  } else {
	  	$fail++;
	  }
  } 
  if ($fail) {
    close $tfh;
    system("cat $tfname 1>&2");
    return undef;
  }

  %$hash_ref=();
  if (!$empty) {
    my $v;
    while(<$tfh>) {
      chomp(my $line=$_);
      next if $line =~ /^ *$/;
	  next if $line =~ /ver*/;
	  if ($db_type eq "oracle"){
		  if (!defined $v) { 
			  $v=$line;
		  } 
		  else {
			  if ($v =~ /(\d+)\.(\d+)/) {
				  my ($nmaj,$nmin) = ($1,$2);
				  if (defined $$hash_ref{$line} && $$hash_ref{$line} =~ /(\d+)\.(\d+)/) {
					  my ($omaj,$omin) = ($1,$2);
					  if ($omaj > $nmaj || ($omaj==$nmaj && $omin >= $nmin)) {
						  $v = undef;
						  next;
					  }
				  }
				  $$hash_ref{$line} = $v;
				  $v = undef;
			  } 
			  else {
				  close $tfh;
				  print STDERR "Unexpected format for schema version number in DB\n";
				  return undef;
			  }
		  }
	  }
	  elsif ($db_type eq "mysql"){
		  if (!defined $v) { 
			  $v=$line;
		  }
		  my @chars = split(' ', $v);
		  my $version = $chars[0];
		  my $component = $chars[1];
		  if ($version =~ /(\d+)\.(\d+)/) {
			  my ($nmaj,$nmin) = ($1,$2);
			  if (defined $$hash_ref{$component} && $$hash_ref{$component} =~ /(\d+)\.(\d+)/) {
				  my ($omaj,$omin) = ($1,$2);
				  if ($omaj > $nmaj || ($omaj==$nmaj && $omin >= $nmin)) {
					  $v = undef;
					  next;
				  }
			  }
			  $$hash_ref{$component} = $version;
			  $v = undef;
		  } 
		  else {
			  close $tfh;
			  print STDERR "Unexpected format for schema version number in DB\n";
			  return undef;
		  }
	  }
	}
  }
  close $tfh;
  return 1;
}

sub glob_strings {
  my ($dbname,$n,$major,$minor,$major2,$minor2) = @_;
  if ($dbname eq "atp") {
    if ($n == 1) {
      return("/usr/share/doc/argo-atp-*/${db_type}_schema/ver_*");
    } elsif ($n == 2) {
		if ($db_type eq "oracle"){
      		return("/usr/share/doc/argo-atp-*/oracle_schema/ver_".$major."_".$minor."/db_schema/CREATE_ATP_SCHEMA.sql");
		}
		if ($db_type eq "mysql"){
			return("/usr/share/doc/argo-atp-*/mysql_schema/ver_".$major."_".$minor."/CREATE_ATP_SCHEMA.sql");
		}
    } elsif ($n == 3) {
      return("/usr/share/doc/argo-atp-*/${db_type}_schema/db_migrate_schema/from_".$major."_".$minor."_to_".$major2."_".$minor2.".sql");
    }
  } elsif ($dbname eq "metricstore") {
    if ($n == 1) {
      return("/usr/share/doc/mrs-*/DBScripts/initial/*");
    } elsif ($n == 2) {
      return("/usr/share/doc/mrs-*/DBScripts/initial/".$major.".".$minor."/${db_type}/CREATE_MRS_SCHEMA.sql");
    } elsif ($n == 3) {
      return("/usr/share/doc/mrs-*/DBScripts/upgrades/".$major2.".".$minor2."/${db_type}/UPGRADE_MRS_SCHEMA.sql");
    }
  } elsif ($dbname eq "ace") {
    if ($n == 1) {
      return("/usr/share/doc/ace-*/schema/oracle/ver_*");
    } elsif ($n == 2) {
      return("/usr/share/doc/ace-*/schema/oracle/ver_".$major."_".$minor."/CREATE_ACE_SCHEMA.sql");
    } elsif ($n == 3) {
      return("/usr/share/doc/ace-*/schema/oracle/db_migrate_schema/from_".$major."_".$minor."_to_".$major2."_".$minor2.".sql");
    }
  } elsif ($dbname eq "poem") {
    if ($n == 1) {
      return("/usr/share/doc/poem-*/poem/schema/${db_type}/initial/*");
    } elsif ($n == 2) {
      return("/usr/share/doc/poem-*/poem/schema/${db_type}/initial/".$major.".".$minor."/create_structure.sql");
    } elsif ($n == 3) {
      return("/usr/share/doc/poem-*/poem/schema/${db_type}/upgrades/".$major2.".".$minor2."/from_".$major."_".$minor."_to_".$major2."_".$minor2.".sql");
    }
  } elsif ($dbname eq "poem_sync") {
    if ($n == 1) {
      return("/usr/share/doc/poem-sync-*/poem_sync/schema/${db_type}/initial/*");
    } elsif ($n == 2) {
      return("/usr/share/doc/poem-sync-*/poem_sync/schema/${db_type}/initial/".$major.".".$minor."/poem_sync_schema.sql");
    } elsif ($n == 3) {
      return("/usr/share/doc/poem-sync-*/poem_sync/schema/${db_type}/upgrades/".$major2.".".$minor2."/upgrade_".$major.".".$minor."_to_".$major2.".".$minor2.".sql");
    }
  } elsif ($dbname eq "dax") {
    if ($n == 1) {
      return("/opt/dax/schema/oracle/ver_*");
    } elsif ($n == 2) {
      return("/opt/dax/schema/oracle/ver_".$major."_".$minor."/scripts/CREATE_DAX_SCHEMA.sql");
    } elsif ($n == 3) {
      return("/opt/dax/schema/oracle/db_migrate_schema/from_".$major."_".$minor."_to_".$major2."_".$minor2.".sql");
    }
  } elsif ($dbname eq "mywlcg") {
    if ($n == 1) {
      return("/usr/share/doc/mywlcg-*/schema/oracle/ver_*");
    } elsif ($n == 2) {
      return("/usr/share/doc/mywlcg-*/schema/oracle/ver_".$major."_".$minor."/CREATE_MYWLCG_SCHEMA.sql");
    } elsif ($n == 3) {
      return("/usr/share/doc/mywlcg-*/schema/oracle/upgrades/from_".$major."_".$minor."_to_".$major2."_".$minor2.".sql");
    }
  }
  return undef;
}

sub find_largest($) {
  my ($aref) = @_;
  my ($major,$minor);
  foreach my $line (@$aref) {
    if ($line =~ /(\d+)[_.](\d+)$/) {
      my ($x,$y) = ($1, $2);
      if (!defined $major || !defined $minor || $major < $x || ($major == $x && $minor < $y)) {
        ($major,$minor) = ($x, $y);
      } elsif ($major == $x && $minor == $y) {
        print STDERR "Unexpected duplicate schema at $line\n";
        exit 1;
      }
    }
  }
  return ($major,$minor);
}

sub dodb($$$$) {
  my ($current_versions,$dbname,$onlycheck,$changedref) = @_;
  my @ary = glob(glob_strings($dbname,1));
  if (scalar(@ary) == 0) {
    if (!$onlycheck && exists $$current_versions{$dbname}) {
      print "\tDid not find a local package containing schema for $dbname. Skipping.\n";
    }
    return;
  }
  my ($tmajor,$tminor) = find_largest(\@ary);
  if (!defined $tmajor || !defined $tminor) {
    print STDERR "Definite schema version not found\n";
    exit 1;
  }
  if (!exists $$current_versions{$dbname}) {
    if ($onlycheck) {
      print STDERR "Could not find any entry for $dbname in schema_details\n";
      exit 1;
    }
    @ary = glob(glob_strings($dbname,2,$tmajor,$tminor));
    if (scalar(@ary) != 1) {
      print STDERR "Could not find $dbname schema create script\n";
      exit 1;
    }
    print "\tCreating $dbname DB version ".$tmajor.".".$tminor."\n";
    unless (run_db_script($ary[0])) {
      print "\tFailed to create DB.\n";
      exit 1;
    }
    $$changedref = 1 if defined $changedref;
  } else {
    my ($major, $minor);
    if ($$current_versions{$dbname} =~ /(\d+)\.(\d+)/) {
      ($major,$minor) = ($1, $2);
    } else {
      print STDERR "Could not identify $dbname version\n";
      exit 1;
    }
    while(1) {
      if ($major >= $tmajor && $minor >= $tminor) {
        print "\t$dbname DB is target version ".$major.".".$minor."\n" if $onlycheck;
        last;
      }
      if ($onlycheck) {
        print STDERR "schema_details for $dbname shows it is not at the highest available version\n";
        exit 1;
      }
      {
        @ary = glob(glob_strings($dbname,3,$major,$minor,$major,$minor+1));
        if (@ary) { $minor++; last; }
        print STDERR "No script to upgrade $dbname DB to version ".$major.".".($minor+1)."\n";
        @ary = glob(glob_strings($dbname,3,$major,$minor,$major+1,0));
        if (@ary) { $major++; $minor=0; last; }
        print STDERR "No script to upgrade $dbname DB to version ".($major+1).".0\n";
        @ary = glob(glob_strings($dbname,3,$major,$minor,$major+1,1));
        if (@ary) { $major++; $minor=1; last; }
        print STDERR "No script to upgrade $dbname DB to version ".($major+1).".1\n";
        @ary = glob(glob_strings($dbname,3,$major,$minor,$tmajor,$tminor));
        if (@ary) { $major=$tmajor; $minor=$tminor; last; }
        print STDERR "No script to upgrade $dbname DB to version ".$tmajor.".".$tminor."\n";
      }
      if (scalar(@ary) == 1) {
        print "\tUpgrading $dbname DB to version ".$major.".".$minor."\n";
        exit 1 unless run_db_script($ary[0]);
        $$changedref = 1 if defined $changedref;
      } elsif (scalar(@ary) > 1) {
        print STDERR "Found more than one schema migrate script for the same version\n";
        exit 1;
      } else {
        print STDERR "Could not find a script to upgrade to target version\n";
        exit 1;
      }
    }
  }
}

my %res;
exit 1 unless get_details(\%res);

if (scalar(keys %res)>0) {
  print "\tExisting DB schema and versions:\n\n";
  for my $k (keys %res) {
  	  print "\t\t- $k is currently $res{$k}\n";
  }
}

my $changed=0;
my @dbs=0;
if ($db_type eq "oracle"){
	@dbs = ("atp", "poem", "poem_sync", "metricstore", "ace", "dax", "mywlcg");
}
elsif($db_type eq "mysql")
{
	@dbs = ("atp", "poem", "poem_sync", "metricstore");
}
for my $db (@dbs) {
  dodb(\%res, $db, 0, \$changed);
}

if ($changed) {
  print "\n\tChanges have been applied.\n";
  print "\tChecking again to verify that schema_details shows db is at the target version:\n\n";

  exit 1 unless get_details(\%res);
  for my $db (@dbs) {
    dodb(\%res, $db, 1, undef);
  }
}

exit 0;
