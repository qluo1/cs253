#!/bin/bash
export BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export RUNNER_DIR=testRunner
cd "$BIN_DIR/.." # should be "TestCases"
if [ -d $RUNNER_DIR ] ; then
{
    mkdir -p $RUNNER_DIR/stats
    mkdir -p $RUNNER_DIR/log
}
else
{
    echo "$RUNNER_DIR vamoos"
}
fi
export ENV="$(echo $2 | tr [:lower:] [:upper:] 2> /dev/null)"

/gns/mw/lang/perl/perl-5.10-6/bin/perl -x $RUNNER_DIR/$(basename $0) $*
exit $?

#!/gns/mw/lang/perl/perl-5.10-6/bin/perl
$|=1;
# line 19 "testRunner.pl"
use warnings;
use strict;
use Data::Dumper;
use File::Copy qw/move copy/;
use File::Path;
use Carp qw/confess/;
use POSIX qw(:sys_wait_h);
use Getopt::Long;
$Data::Dumper::Indent = 1;
$Data::Dumper::Sortkeys = 1;
my $run_dir = $ENV{RUNNER_DIR};

my %envs = (qae=>1, pme=>1, ppe=>1);
my %timesets = (normal=>1, pre_cspa=>1);

my $do_progress_report = 0;
my $date = '';

my $optres = GetOptions(
    "report|r" => \$do_progress_report,
    "date|d=s" => \$date,
);
if (! $optres)
{
    confess("Problems parsing command line: $!");
}

my ($env, $timeset, $max_runs, $max_forks) = @ARGV;

if (! defined $env || ! exists $envs{$env})
{
    confess("Please start with a valid environment as param 1 (" . join(", ", keys(%envs)) . ")");
}

if (! defined $timeset || ! exists $timesets{$timeset})
{
    confess("Please start with a valid timeset as param 2 (" . join(", ", keys(%timesets)) . ")");
}

if (! $do_progress_report && (! defined $max_runs || $max_runs !~ /\d+/ || $max_runs == 0))
{
    confess("Please provide a postitive integer for param 3 (max_runs)");
}

if (! $do_progress_report && (! defined $max_forks || $max_forks !~ /\d+/ || $max_forks == 0))
{
    confess("Please provide a postitive integer for param 4 (max_forks)");
}

$ENV{ENV} = uc($env);

sub today
{
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday)=localtime(time);
    $year=sprintf("%04d",$year+1900);
    $mon=sprintf("%02d",$mon);
    $mon++;
    $mday=sprintf("%02d",$mday);
    return "$year$mon$mday";
}

sub time_now
{
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday)=localtime(time);
    $hour=sprintf("%02d",$hour);
    $min=sprintf("%02d",$min);
    $sec=sprintf("%02d",$sec);
    return "$hour$min$sec";
}

sub disp_time_now
{
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday)=localtime(time);
    $hour=sprintf("%02d",$hour);
    $min=sprintf("%02d",$min);
    $sec=sprintf("%02d",$sec);
    return "$hour-$min-$sec";
}


sub get_test_definitions
{
    my %tests;
    open PH, "$run_dir/listTests.py |";
    foreach my $line(<PH>)
    {
        print ">> $line";
        chomp $line;
        my ($file, $class, $function) = split(" ", $line);
        if (! defined $function || $function eq "")
        {
            $function = $class;
            $class = "";
        }
        $tests{$file}{$class}{$function} = 1;
    }
    close PH;
    return %tests;
}

sub get_run_stats($$$$)
{
    my ($file, $class, $function, $date) = @_;
    my $statdir = "$run_dir/stats/$date";
    my $statfile = "$statdir/$file.$class.$function.$date";
    my $success = 0;
    my $runs = 0;
    my $time = 0;
    if (-f $statfile)
    {
        open IH, "<", $statfile;
        while(my $line = <IH>)
        {
            chomp $line;
            if ($line)
            {
                ($success, $runs, $time) = split /:/, $line;
            }
        }
        close IH;
    }
    return ($success, $runs, $time);
}

sub set_run_stats($$$$$$)
{
    my $time = disp_time_now();
    my ($file, $class, $function, $today, $success, $runs) = @_;
    mkdir("$run_dir/stats");
    my $statdir = "$run_dir/stats/$today";
    mkdir("$statdir");
    my $statfile = "$statdir/$file.$class.$function.$today";
    open OH, ">>", $statfile;
    print OH "$success:$runs:$time\n";
    close OH;
}

sub get_env_tests($$$)
{
    my ($env, $when, $date) = @_;
    my %env_tests = ();
    my %all_tests = get_test_definitions();
    open IH, "<", "$run_dir/setup/tests_by_env" or confess("Can't read from file tests_by_env: $!");
    foreach my $line(<IH>)
    {
        $line=~s/^\s+|\s+$|\r|\n//g;
        $line =~ s/#.*//g;
        next if ! defined $line || $line eq "";
        my ($file_name, $class_pattern, $function_pattern, $envs_string, $instruction, $suitable_times, $deprecated) = split /:/, $line;
        $file_name =~ s/^\s+|\s+$//g;
        $class_pattern =~ s/^\s+|\s+$//g;
        $function_pattern =~ s/^\s+|\s+$//g;
        $envs_string =~ s/^\s+|\s+$//g;
        $instruction =~ s/^\s+|\s+$//g;
        $suitable_times =~ s/^\s+|\s+$//g;
        if ($when !~ /$suitable_times/)
        {
            # print "THuNK : $file_name, $class_pattern, $function_pattern\n";
            next;
        }
        
        if (defined $deprecated)
        {
            $deprecated =~ s/^\s+|\s+$//g;
        }

        if (! exists $all_tests{$file_name})
        {
            print Dumper(\%all_tests);
            confess("File [$file_name] not defined in test definitions");
        }
        # next if $envs_string !~ /$env/;
        my $matched = 0;
        foreach my $class(keys %{$all_tests{$file_name}})
        {
            if ($class =~ /$class_pattern/)
            {
                foreach my $function(keys %{$all_tests{$file_name}{$class}})
                {

                    if ($function =~ /$function_pattern/)
                    {
                        $matched = 1;

                        if ($envs_string =~ /$env/ && defined $deprecated && $deprecated eq "deprecated")
                        {
                            print "Setup - Deprecated for $file_name:$class:$function\n";
                            $env_tests{exclude}{$file_name}{$class}{$function} = -1;
                            next;
                        }
                        if ($instruction eq "no" && $envs_string =~ /$env/)
                        {
                            # Explicit exclude for environment
                            print "Setup - Explicit no on $file_name:$class:$function\n";
                            $env_tests{exclude}{$file_name}{$class}{$function} = 1;
                            #$env_tests{include}{$file_name}{$class}{$function} = 0;
                        }
                        elsif ($instruction eq "yes" && $envs_string =~ /$env/)
                        {
                            print "Setup - Explicit yes on $file_name:$class:$function\n";
                            # Explicit include for environment
                            $env_tests{include}{$file_name}{$class}{$function} = 1;
                        }
                        else
                        {
                            if ($envs_string =~ /$env/)
                            {
                                # Explicit 'no'
                                # THIS SHOULD BE CRUFT
                                print "Setup - Explicit no v2 on $file_name:$class:$function\n";
                                $env_tests{exclude}{$file_name}{$class}{$function} = 1;
                            }
                            else
                            {
                                if ($instruction eq "yes")
                                {
                                    # Excluded by omission
                                    print "Setup - Omission of $file_name:$class:$function\n";
                                    $env_tests{exclude}{$file_name}{$class}{$function} = 1;
                                }
                                else
                                {
                                    # An explicit 'no' which didn't involve us - pass
                                }
                            }
                        }
                    }
                }
            }
        }
        if (! $matched)
        {
            confess("No tests matched rule definition [$line]");
        }
    }
    close IH;
    $env_tests{enabled_count} = 0;
    foreach my $file(keys %{$env_tests{include}})
    {
        foreach my $class(keys %{$env_tests{include}{$file}})
        {
            foreach my $function(keys %{$env_tests{include}{$file}{$class}})
            {
                if ($env_tests{include}{$file}{$class}{$function} == 1)
                {
                    $env_tests{enabled_count}++;
                }
            }
        }
    }
    return %env_tests;
}

sub run_test($$$$$)
{
    $|=1;
    my ($file, $class, $function, $today, $run_number) = @_;
    my $name = "$file.$class.$function.$run_number:$$";
    local $SIG{HUP}  =  sub { print "Child $name:BUNT! HUP\n";  set_run_stats($file, $class, $function, $today, 0, $run_number); exit 1; };
    local $SIG{INT}  =  sub { print "Child $name:BUNT! INT\n";  set_run_stats($file, $class, $function, $today, 0, $run_number); exit 1; };
    local $SIG{QUIT}  = sub { print "Child $name:BUNT! QUIT\n"; set_run_stats($file, $class, $function, $today, 0, $run_number); exit 1; };
    set_run_stats($file, $class, $function, $today, -1, $run_number+1);
    my $cmd;
    if ($class eq "")
    {
       $cmd = "bin/run_pytest.bash tests/om2/$file -k '$function' -v --tb long --showlocals --reruns 3";
    }
    else
    {
       $cmd = "bin/run_pytest.bash tests/om2/$file -k '$class and $function' -v --tb long --showlocals --reruns 3";
    }
    print "Child $name: $cmd\n";
    open PH, "$cmd 2>&1 |";
    mkpath("testRunner/log/$today");
    my $output_file = "testRunner/log/$today/$file.$class.$function.$today.$run_number";
    open OH, ">", $output_file;
    my $report_file = "";
    while( my $line = <PH>)
    {
        print OH $line;
        if ($line =~ /^ generated html file:/)
        {
            ($report_file) = $line =~ /\/reports\/(.*\.html)/;
            print "Child $name:Report [$report_file]\n";
        }
        elsif ($line =~/no test report generated for the run/)
        {
        }
        # TODO: catch MORE interesting lines
    }
    close OH;
    close PH;
    my $retcode = $?;
    $retcode = $retcode >> 8;
    my $report_dir = "reports/$today";
    mkpath("$report_dir/gold");  # For our passed test runs
    mkpath("$report_dir/brown"); # For our failed runs
    if ($retcode == 0)
    {
        print "Child $name:Success\n";
        set_run_stats($file, $class, $function, $today, 1, $run_number+1);
        if ($report_file eq "")
        {
            # Something has gone wrong - returned 0 to shell but did not generate a report
            # ... that's pretty brown right there
            copy($output_file, "$report_dir/brown/$file.$class.$function.$today.$run_number.txt");
        }
        else
        {
            move("reports/$report_file", "$report_dir/gold/$file.$class.$function.$today.$run_number.html");
        }
    }
    else
    {
        if ($report_file eq "")
        {
            copy($output_file, "$report_dir/brown/$file.$class.$function.$today.$run_number.txt");
        }
        else
        {
            move("reports/$report_file", "$report_dir/brown/$file.$class.$function.$today.$run_number.html");
        }
        if ($run_number + 1 > $max_runs)
        {
            print "Child $name:Fail (final)\n";
            set_run_stats($file, $class, $function, $today, -2, $run_number+1);
        }
        else
        {
            print "Child $name:Fail (and re-run)\n";
            set_run_stats($file, $class, $function, $today, 0, $run_number+1);
        }
    }
    exit $retcode;
}

sub get_test_status($$)
{
    my ($include, $date) = @_;
    my %status = ();
    $status{finished} = {};
    $status{unfinished} = {};
    $status{finished_count} = 0;
    $status{unfinished_count} = 0;
    $status{ok_count} = 0;
    $status{failed_count} = 0;
    $status{running_count} = 0;
    $status{running} = {};
    foreach my $file(keys %{$include->{include}})
    {
        foreach my $class(keys %{$include->{include}->{$file}})
        {
            foreach my $function(keys %{$include->{include}->{$file}->{$class}})
            {
                my ($success, $runs, $time) = get_run_stats($file, $class, $function, $date);
                if ($success == 1)
                {
                    $status{finished_count}++;
                    $status{ok_count}++;
                    $status{finished}{$file}{$class}{$function}{runs} = $runs;
                    $status{finished}{$file}{$class}{$function}{time} = $time;
                    $status{finished}{$file}{$class}{$function}{success} = $success;
                }
                elsif ($success == -1)
                {
                    $status{running_count}++;
                    $status{running}{$file}{$class}{$function}{runs} = $runs;
                    $status{unfinished_count}++;
                    #$status{unfinished}{$runs}{$file}{$class}{$function}{time} = $time;
                    #$status{unfinished}{$runs}{$file}{$class}{$function}{success} = $success;
                }
                elsif ($success == -2)
                {
                    # max_runs exceeded
                    $status{failed_count}++;
                    $status{finished_count}++;
                    $status{finished}{$file}{$class}{$function}{runs} = $runs;
                    $status{finished}{$file}{$class}{$function}{time} = $time;
                    $status{finished}{$file}{$class}{$function}{success} = $success;
                }
                else
                {
                    $status{unfinished_count}++;
                    $status{unfinished}{$runs}{$file}{$class}{$function}{time} = $time;
                    $status{unfinished}{$runs}{$file}{$class}{$function}{success} = $success;
                }
            }
        }
    }
    return %status;
}
if ($date eq "")
{
    $date = today();
}
my %tests_to_run = get_env_tests($env, $timeset, $date);
if ($do_progress_report)
{
    my $server_time = `/usr/sbin/zdump /etc/localtime`;
    chomp $server_time;
    my $exchange_time = `/usr/sbin/zdump /usr/share/zoneinfo/Australia/Sydney`;
    chomp $exchange_time;
    $server_time =~ s/^\/\S+\s+//g;
    $exchange_time =~ s/^\/\S+\s+//g;
    my %test_status = get_test_status(\%tests_to_run, $date);
    print Dumper(\%test_status);
    print "Server time: $server_time   Exchange time: $exchange_time\n\n";
    system("crontab -l | grep testRunner");
    print "\nRUNNING:\n";
    foreach my $file(keys %{$test_status{running}})
    {
        foreach my $class(keys %{$test_status{running}{$file}})
        {
            foreach my $function(keys %{$test_status{running}{$file}{$class}})
            {
                my $run_count = $test_status{running}{$file}{$class}{$function}{runs};
                print "  $file.$class.$function - ${run_count}stndrdth run\n";
            }
        }

    }
    my @passed;
    my @failed;
    my @pending;
    foreach my $file(keys %{$test_status{finished}})
    {
        foreach my $class(keys %{$test_status{finished}{$file}})
        {
            foreach my $function(keys %{$test_status{finished}{$file}{$class}})
            {
                my $run_count = $test_status{finished}{$file}{$class}{$function}{runs};
                my $success = $test_status{finished}{$file}{$class}{$function}{success};
                if ($success == -2)
                {
                    push @failed, "  $file.$class.$function - ${run_count} runs";
                }
                elsif ($success == 1)
                {
                    push @passed, "  $file.$class.$function - ${run_count} runs";
                }
            }
        }

    }
    foreach my $run_count(keys %{$test_status{unfinished}})
    {
    foreach my $file(keys %{$test_status{unfinished}{$run_count}})
    {
        foreach my $class(keys %{$test_status{unfinished}{$run_count}{$file}})
        {
            foreach my $function(keys %{$test_status{unfinished}{$run_count}{$file}{$class}})
            {
                #my $run_count = $test_status{unfinished}{$file}{$class}{$function}{runs};
                #my $success = $test_status{unfinished}{$run_count}{$file}{$class}{$function}{success};
                push @pending, "  ${run_count} runs - $file.$class.$function";
            }
        }
    }
    }
    
    print "\nPASSED:\n";
    print (join("\n", @passed) . "\n");
    print "\nFAILED:\n";
    print (join("\n", @failed) . "\n");
    print "\nPENDING:\n";
    print (join("\n", @pending) . "\n");

    exit;
}

my $finished = 0;
my %running_pids = ();
# exit;
while (1)
{
    my %test_status = get_test_status(\%tests_to_run, $date);
    if ($test_status{unfinished_count} == 0 && $test_status{running_count} == 0)
    {
        last;
    }
    if (scalar(keys(%running_pids)) < $max_forks)
    {
        my ($file, $class, $function, $run_number);
        
        TEST_SELECT: foreach my $run_number_cmp(sort {$a <=> $b} keys %{$test_status{unfinished}})
        {
            foreach my $file_cmp(keys %{$test_status{unfinished}{$run_number_cmp}})
            {
                foreach my $class_cmp(keys %{$test_status{unfinished}{$run_number_cmp}{$file_cmp}})
                {
                    foreach my $function_cmp(keys %{$test_status{unfinished}{$run_number_cmp}{$file_cmp}{$class_cmp}})
                    {
                        if ($test_status{unfinished}{$run_number_cmp}{$file_cmp}{$class_cmp}{$function_cmp}{success} == 0) # Not already running (-1)
                        {
                            $file = $file_cmp;
                            $class = $class_cmp;
                            $run_number = $run_number_cmp;
                            $function = $function_cmp;
                            print "RUNNER:Selected $file:$class:$function run $run_number\n";

                            last TEST_SELECT;
                        }
                    }
                }
            }
            print "RUNNER:No selection made\n";
        }
        if (defined $function)
        {
            print "RUNNER:function=$function, file=$file, class=$class, function=$function\n";
            my $pid = fork();
            if ($pid)
            {
                $running_pids{$pid} = "$file\:\:$class\:\:$function (run " . ($run_number + 1) . ")";
            }
            else
            {
                print "Child $$: Scraped params = (file=$file, class=$class, function=$function, date=$date, run_number=$run_number)\n";
                run_test($file, $class, $function, $date, $run_number);
            }
        }
        else
        {
            # Do nothing, no tests selected
        }
    }
    foreach my $pid(keys %running_pids)
    {
        my $waitres = waitpid($pid, WNOHANG);
        my $test_name = $running_pids{$pid};
        if ($waitres == -1)
        {
            delete $running_pids{$pid};
        }
        else
        {
            if ($waitres eq $pid)
            {
                my $retcode=$?;
                $retcode = $retcode >> 8 ;
                if ($retcode != 0)
                {
                    print "RUNNER:Pantalones, $test_name\n";
                }
            }
            else
            {
            }
        }
    }
    sleep 1;
    print "RUNNER:Ponk!\n";
}
print "RUNNER:Outies\n";
