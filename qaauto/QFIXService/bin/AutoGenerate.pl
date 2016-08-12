#!/usr/bin/perl 
use File::Basename;
use Data::Dumper;

#use lib "/home/omaqa/runtime/client/Excel-FixSim/lib/library/blib_IO/lib";
#use lib "/home/omaqa/runtime/client/Excel-FixSim/lib/library/blib_parse/lib";
#use lib "/home/omaqa/runtime/client/Excel-FixSim/lib/library/blib_OLE/lib";
use Spreadsheet::ParseExcel;
use File::Basename;
my $start_dir = $ARGV[0];

my $home_path=$start_dir."/";

$file = $home_path."/TC.xls";
print  $file;
$rawfile = $home_path."RawCombinedUnitTests.txt";
$logfile = $home_path."ExcelSim.log"; 

#use strict;

print LOGFILE  "started";
my $enum_ints = 1;
my $filename = $file;
#my $filename = shift || "demo.xls";

#my $priceDataFile = '../config/PriceControl.data';
my $priceDataFile = $home_path.'/PriceControl.data';

open (my $fd, $priceDataFile) || die("Could not open priceDataFile\n");

my @symData;
my $i = 0;
while(my $row = <$fd>)
{
    print $row."\n";
    my @word = split /[:\n]/, $row;
    $symData[$i][0] = $word[0];
    $symData[$i][1] = $word[1];
    $i++;
}
close($fd);

print Dumper \@symData;

my $e = new Spreadsheet::ParseExcel;
my $eBook = $e->Parse($filename);

my $sheets = $eBook->{SheetCount};
my ($eSheet_Gen, $sheetName_Gen);

    my $action_no = 0;
    my $test_case_no = 0;
    my $action = '';
    my $acn_data = '';
    my $txn_no = 0;
    $eSheet_Gen = $eBook->{Worksheet}[0];
    $sheetName_Gen = $eSheet_Gen->{Name};
    print "Worksheet $sheet: $sheetName_Gen\n";
    next unless (exists ($eSheet_Gen->{MaxRow}) and (exists ($eSheet_Gen->{MaxCol})));
    #foreach my $row (1 .. $eSheet_Gen->{MaxRow}) {
    open(RAWFILE, ">$rawfile") || die ("Cannot open Raw CombinedUnitTests.py\n");
    open(LOGFILE, ">$logfile") || die ("Cannot open Log File\n");
    my $symbol='';
    my $new_price = 0;
    #print RAWFILE "sampleFixLogon.py\n";
    for ($row = 1; $row <= $eSheet_Gen->{MaxRow}; $row++) {

		#Check if Row zero is Not-null which indicate start of a test case
		if ((defined $eSheet_Gen->{Cells}[$row][0])) {
            $str_number=$eSheet_Gen->{Cells}[$row][0]->Value;
            if($str_number=~/{DNR}/){
            print LOGFILE "Ignoring test case:".$eSheet_Gen->{Cells}[$row][1]->Value."\n";
            }
            else{
			print LOGFILE "\nStart of Test Case\n";
			$test_case_no = $test_case_no + 1;
			$tc_start = 1;
            }
		}

        #Check if the test case has started and the tc name is defined 
		if (($tc_start eq 1) && (defined $eSheet_Gen->{Cells}[$row][4])){
		if ($eSheet_Gen->{Cells}[$row][4]->Value ne '') {
			$txn_no = 0 ;
                        $tc_name = $eSheet_Gen->{Cells}[$row][4]->Value;
                        print LOGFILE "TC Name:".$tc_name."\n";
            $testcasefile = $home_path.$tc_name.".py";
            print $testcasefile;
			open(TCFILE, ">$testcasefile") || die ("Cannot open Test Case File\n");
			print RAWFILE "$tc_name".".py\n";
		}
                }

        #Fetch TC description
		if ($tc_start eq 1 &&  defined $eSheet_Gen->{Cells}[$row][1]){
		if ($eSheet_Gen->{Cells}[$row][1]->Value ne '') {
			$desc = $eSheet_Gen->{Cells}[$row][1]->Value;
			print LOGFILE "Description:".$desc."\n";
			write_tc_header($desc);
		}
		}

        #Get ACtions from field 5 and process them 
		if ($tc_start eq 1 &&  defined $eSheet_Gen->{Cells}[$row][5]) {
		if ($eSheet_Gen->{Cells}[$row][5]->Value ne '') {
			$action = $eSheet_Gen->{Cells}[$row][5]->Value;
			print LOGFILE $action."\n";
			if ( $action eq 'BOTC' ) {
			$row--;
			}
			if ( $action eq 'EOTC' ) {
			$tc_start = 0;
			$row--;
            $symbol='';
            $new_price = 0;
			for ( $i=1; $i < $txn_no+1 ; $i++ )
			{
				print TCFILE "\t\ttestScenario.append(FixMessage_$i.testCaseData())\n";
			}
			print TCFILE "\treturn testScenario\n";
			close(TCFILE);
			}

			if ( $action eq 'New Order' ) {
				$txn_no = $txn_no + 1;
                $acn_side = getSide($row);
                if ( $acn_side eq 'Buy') {
                    print TCFILE "\t\torderId = ordId + 'B'\n";
                }
                else
                {
                    print TCFILE "\t\torderId = ordId + 'S'\n";
                }
    
				print TCFILE "\t\tFixMessage_$txn_no  = engineState.createTestCase(testCaseName)\n";
				print TCFILE "\t\tFixMessage_$txn_no.addMessageFromCustomer(connectionId, 'Order - Single',orderId ,\n";
				print TCFILE "\t\t{\n";
                foreach my $column (6 .. $eSheet_Gen->{MaxCol})
                {
                    if ($eSheet_Gen->{Cells}[$row][$column]->Value eq 'SecurityID')
                        {
                            $symbol = $eSheet_Gen->{Cells}[$row+1][$column]->Value;
                            last;
                        }
                }
                foreach my $row (@symData)
                {
                    if ($row->[0] eq $symbol)
                    {
                        $new_price = $row->[1];
                        last;
                    }
                }
			}

			if ( $action eq 'New Order Ack' ) {
                $acn_side = getSide($row);
                if ( $acn_side eq 'Buy') {
                    print TCFILE "\t\torderId = ordId + 'B'\n";
                }
                else
                {
                    print TCFILE "\t\torderId = ordId + 'S'\n";
                }
                print TCFILE "\t\torigOrderId = orderId\n";
				print TCFILE "\t\tFixMessage_$txn_no.addMessageToCustomer(connectionId, 'Execution Report', orderId, 'ClOrdID', \n";
                                print TCFILE "\t\t{\n";
           }

           if ( $action eq 'Full Fill' ) {
                $acn_side = getSide($row);
                if ( $acn_side eq 'Buy') {
                    print TCFILE "\t\torderId = ordId + 'B'\n";
                }
                else
                {
                    print TCFILE "\t\torderId = ordId + 'S'\n";
                }
                print TCFILE "\t\tFixMessage_$txn_no.addMessageToCustomer(connectionId, 'Execution Report', orderId, 'ClOrdID', \n";
                                print TCFILE "\t\t{\n";
           }

           if ( $action eq 'Partial Fill' ) {
                $acn_side = getSide($row);
                if ( $acn_side eq 'Buy') {
                    print TCFILE "\t\torderId = ordId + 'B'\n";
                }
                else
                {
                    print TCFILE "\t\torderId = ordId + 'S'\n";
                }
                print TCFILE "\t\tFixMessage_$txn_no.addMessageToCustomer(connectionId, 'Execution Report', orderId, 'ClOrdID', \n";
                print TCFILE "\t\t{\n";
           }

    		if ( $action eq 'New Order Reject' ) {
                $acn_side = getSide($row);
                if ( $acn_side eq 'Buy') {
                    print TCFILE "\t\torderId = ordId + 'B'\n";
                }
                else
                {
                    print TCFILE "\t\torderId = ordId + 'S'\n";
                }
                print TCFILE "\t\torigOrderId = orderId\n";
                                print TCFILE "\t\tFixMessage_$txn_no.addMessageToCustomer(connectionId, 'Execution Report', orderId, 'ClOrdID', \n";
                                print TCFILE "\t\t{\n";
           }


			if ( $action eq 'Prod Not Found Rej' ) {
                                print TCFILE "\t\tFixMessage_$txn_no.addMessageToCustomer(connectionId, 'Execution Report', orderId, 'ClOrdID', \n";
                                print TCFILE "\t\t{\n";
            }


			if ( $action eq 'Amend Order' ) {
                $acn_side = getSide($row);
                if ( $acn_side eq 'Buy') {
                    print TCFILE "\t\torderId = ordId + 'B'\n";
                    print TCFILE "\t\torigOrderId = orderId\n";
                    print TCFILE "\t\torderId = orderId + 'G'\n";
                }
                else
                {
                    print TCFILE "\t\torderId = ordId + 'S'\n";
                    print TCFILE "\t\torigOrderId = orderId\n";
                    print TCFILE "\t\torderId = orderId + 'G'\n";
                }
                $txn_no = $txn_no + 1;
                                print TCFILE "\t\tFixMessage_$txn_no  = engineState.createTestCase(testCaseName)\n";
                                print TCFILE "\t\tFixMessage_$txn_no.addMessageFromCustomer(connectionId, 'Order Cancel/Replace Request',orderId ,\n";
                                print TCFILE "\t\t{\n";
              }

                       if ( $action eq 'Amend Order Ack' ) {
                                $acn_side = getSide($row);
                             if ( $acn_side eq 'Buy') {
                               print TCFILE "\t\torderId = ordId + 'B'\n";
                               print TCFILE "\t\torigOrderId = orderId\n";
                               print TCFILE "\t\torderId = orderId + 'G'\n";
                             }
                       else
                      {
                           print TCFILE "\t\torderId = ordId + 'S'\n";
                           print TCFILE "\t\torigOrderId = orderId\n";
                           print TCFILE "\t\torderId = orderId + 'G'\n";
                      }
                                print TCFILE "\t\tFixMessage_$txn_no.addMessageToCustomer(connectionId, 'Execution Report', orderId , 'ClOrdID', \n";
                                print TCFILE "\t\t{\n";
                        }
	   if ( $action eq 'Done For Day' ) {
                                $acn_side = getSide($row);
                             if ( $acn_side eq 'Buy') {
                               print TCFILE "\t\torderId = ordId + 'B'\n";
                               print TCFILE "\t\torigOrderId = orderId\n";
                               #print TCFILE "\t\torderId = orderId + 'G'\n";
                             }
                       else
                      {
                           print TCFILE "\t\torderId = ordId + 'S'\n";
                           print TCFILE "\t\torigOrderId = orderId\n";
                           #print TCFILE "\t\torderId = orderId + 'G'\n";
                      }
                                print TCFILE "\t\tFixMessage_$txn_no.addMessageToCustomer(connectionId, 'Execution Report', orderId , 'ClOrdID', \n";
                                print TCFILE "\t\t{\n";
                        }

            if ( $action eq 'Amend Pend Ack' ) {
                                $acn_side = getSide($row);
                             if ( $acn_side eq 'Buy') {
                               print TCFILE "\t\torderId = ordId + 'B'\n";
                               print TCFILE "\t\torigOrderId = orderId\n";
                               print TCFILE "\t\torderId = orderId + 'G'\n";
                             }
                       else
                      {
                             print TCFILE "\t\torderId = ordId + 'S'\n";
                             print TCFILE "\t\torigOrderId = orderId\n";
                             print TCFILE "\t\torderId = orderId + 'G'\n";
                      }
                                print TCFILE "\t\tFixMessage_$txn_no.addMessageToCustomer(connectionId, 'Execution Report', orderId , 'ClOrdID', \n";
                                print TCFILE "\t\t{\n";
                        }

            if ( $action eq 'Amend Cancel Rej' ) {
                                $acn_side = getSide($row);
                             if ( $acn_side eq 'Buy') {
                              print TCFILE "\t\torderId = ordId + 'B'\n";
                              print TCFILE "\t\torigOrderId = orderId\n";
                              print TCFILE "\t\torderId = orderId + 'G'\n";
                             }
                            if ($acn_side eq 'Sell') {
                             print TCFILE "\t\torderId = ordId + 'S'\n";
                             print TCFILE "\t\torigOrderId = orderId\n";
                             print TCFILE "\t\torderId = orderId + 'G'\n";
                            }
                            if ($acn_side eq 'None') {
                             print TCFILE "\t\torderId = ordId + 'B'\n";
                             print TCFILE "\t\torigOrderId = orderId\n";
                             print TCFILE "\t\torderId = orderId + 'G'\n";
                            }
                                print TCFILE "\t\tFixMessage_$txn_no.addMessageToCustomer(connectionId, 'Order Cancel Reject', orderId , 'ClOrdID', \n";
                                print TCFILE "\t\t{\n";
                        }
	    if ( $action eq 'Amend Sell Cancel Rej' ) {
                              print TCFILE "\t\torderId = ordId + 'S'\n";
                              print TCFILE "\t\torigOrderId = orderId\n";
                              print TCFILE "\t\torderId = orderId + 'G'\n";
                              print TCFILE "\t\tFixMessage_$txn_no.addMessageToCustomer(connectionId, 'Order Cancel Reject', orderId , 'ClOrdID', \n";
                              print TCFILE "\t\t{\n";
                        }

            if ( $action eq 'Cancel Rej' ) {
                                $acn_side = getSide($row);
                             if ( $acn_side eq 'Buy') {
                              print TCFILE "\t\torderId = ordId + 'B'\n";
                              print TCFILE "\t\torigOrderId = orderId\n";
                              print TCFILE "\t\torderId = orderId + 'F'\n";
                             }
                            if ($acn_side eq 'Sell') {
                             print TCFILE "\t\torderId = ordId + 'S'\n";
                             print TCFILE "\t\torigOrderId = orderId\n";
                             print TCFILE "\t\torderId = orderId + 'F'\n";
                            }
                            if ($acn_side eq 'None') {
                             print TCFILE "\t\torderId = ordId + 'B'\n";
                             print TCFILE "\t\torigOrderId = orderId\n";
                             print TCFILE "\t\torderId = orderId + 'F'\n";
                            }
                                print TCFILE "\t\tFixMessage_$txn_no.addMessageToCustomer(connectionId, 'Order Cancel Reject', orderId , 'ClOrdID', \n";
                                print TCFILE "\t\t{\n";
                        }

			if ( $action eq 'Cancel Order' ) {
                                $txn_no = $txn_no + 1;
                                $acn_side = getSide($row);
                if ( $acn_side eq 'Buy') {
                               print TCFILE "\t\torderId = ordId + 'B'\n";
                              print TCFILE "\t\torigOrderId = orderId\n";
                                print TCFILE "\t\torderId = orderId + 'F'\n";
                             }
                       else
                      {
                             print TCFILE "\t\torderId = ordId + 'S'\n";
                           print TCFILE "\t\torigOrderId = orderId\n";
                          print TCFILE "\t\torderId = orderId + 'F'\n";
                      }
                                print TCFILE "\t\tFixMessage_$txn_no  = engineState.createTestCase(testCaseName)\n";
                                print TCFILE "\t\tFixMessage_$txn_no.addMessageFromCustomer(connectionId, 'Order Cancel Request',orderId ,\n";
                                print TCFILE "\t\t{\n";
                        }
                        if ( $action eq 'Cancel Ack' ) {
                        $acn_side = getSide($row);
                        if ( $acn_side eq 'Buy') {
                               print TCFILE "\t\torderId = ordId + 'B'\n";
                               print TCFILE "\t\torigOrderId = orderId\n";
                               print TCFILE "\t\torderId = orderId + 'F'\n";
                             }
                       else
                      {
                             print TCFILE "\t\torderId = ordId + 'S'\n";
                           print TCFILE "\t\torigOrderId = orderId\n";
                            print TCFILE "\t\torderId = orderId + 'F'\n";
                        }
                       
                                print TCFILE "\t\tFixMessage_$txn_no.addMessageToCustomer(connectionId, 'Execution Report', orderId , 'ClOrdID', \n";
                                print TCFILE "\t\t{\n";
                        }
                        if ( $action eq 'Cancel Pend Ack' ) {
                        $acn_side = getSide($row);
                        if ( $acn_side eq 'Buy') {
                               print TCFILE "\t\torderId = ordId + 'B'\n";
                               print TCFILE "\t\torigOrderId = orderId\n";
                               print TCFILE "\t\torderId = orderId + 'F'\n";
                             }
                       else
                      {
                             print TCFILE "\t\torderId = ordId + 'S'\n";
                           print TCFILE "\t\torigOrderId = orderId\n";
                            print TCFILE "\t\torderId = orderId + 'F'\n";
                        }

                                print TCFILE "\t\tFixMessage_$txn_no.addMessageToCustomer(connectionId, 'Execution Report', orderId , 'ClOrdID', \n";
                                print TCFILE "\t\t{\n";
                        }
		}
		}

		foreach my $column (6 .. $eSheet_Gen->{MaxCol}) {
		if ($tc_start eq 1 &&  defined $eSheet_Gen->{Cells}[$row][$column] && defined $eSheet_Gen->{Cells}[$row+1][$column]) {
                if ($eSheet_Gen->{Cells}[$row][$column]->Value ne '' &&  $eSheet_Gen->{Cells}[$row+1][$column]->Value ne '') {
			$acn_data =  $eSheet_Gen->{Cells}[$row+1][$column]->Value;
			if ( $acn_data=~/\(\)/ )
			{
				print TCFILE "\t\t\t'".$eSheet_Gen->{Cells}[$row][$column]->Value."': Atr.".$acn_data.",\n";
			}
			else
			{
				if ( $eSheet_Gen->{Cells}[$row][$column]->Value eq 'ClOrdID' || $eSheet_Gen->{Cells}[$row][$column]->Value eq 'OrigClOrdID' )
				{
					print TCFILE "\t\t\t'".$eSheet_Gen->{Cells}[$row][$column]->Value."':".$eSheet_Gen->{Cells}[$row+1][$column]->Value.",\n";
			    	}
                		elsif ( $eSheet_Gen->{Cells}[$row][$column]->Value eq 'Price' || $eSheet_Gen->{Cells}[$row][$column]->Value eq 'StopPx' )
                		{
                    			if ( $eSheet_Gen->{Cells}[$row+1][$column]->Value eq 'ZERO' )
                    			{
                    				print TCFILE "\t\t\t'".$eSheet_Gen->{Cells}[$row][$column]->Value."':'";
                    				print TCFILE "0',\n";
                    			}
                    			elsif ( $eSheet_Gen->{Cells}[$row+1][$column]->Value eq 'NEG' )
                    			{
                    				print TCFILE "\t\t\t'".$eSheet_Gen->{Cells}[$row][$column]->Value."':'";
                    				print TCFILE "-".$new_price."',\n";
                    			}
                    			else
                    			{
                	    			print TCFILE "\t\t\t'".$eSheet_Gen->{Cells}[$row][$column]->Value."':'";
                	    			print TCFILE $new_price+$eSheet_Gen->{Cells}[$row+1][$column]->Value."',\n";
                			}
				}
			    	else 
				{
                        		print TCFILE "\t\t\t'".$eSheet_Gen->{Cells}[$row][$column]->Value."':'".$eSheet_Gen->{Cells}[$row+1][$column]->Value."',\n";
			    	}
			}
                }
                }
		}
		if ($tc_start eq 1 and $action ne 'BOTC' and $action ne 'EOTC'){
		print TCFILE "\t\t}\n";
		print TCFILE "\t\t)\n";
		}
		$row=$row+1;
	}

#close(TCFILE);
#print RAWFILE "sampleFixLogout.py\n";
close(RAWFILE);
print LOGFILE "finished";
close(LOGFILE);

sub write_tc_header{
  print TCFILE "from OmEngineState import OmEngineState\n";
  print TCFILE "from OmOrder import OmOrder\n";
  print TCFILE "import OmTestCase\n";
  print TCFILE "import os;\n";
  print TCFILE "import time;\n";
  print TCFILE "import apolloTestUtilities;\n";
  print TCFILE "def create(engineState, numTests, compId, targetId,Atr):\n";
  print TCFILE "\t\"this is the public interface, called by omsimulator.py\"\n";
  print TCFILE "\ttestScenario = []\n";
  print TCFILE "\ttestCaseName = \"$_[0]\"\n";
  print TCFILE "\ttestWithFix = True\n";
  print TCFILE "\ttestLogFile = False\n";
  print TCFILE "\tconnectionId = compId + '.' + targetId\n";
  print TCFILE "\tfor i in range\(numTests\):\n";
  print TCFILE "\t\tmessageId=i\n";
  #print TCFILE "\t\torderId = Atr.getOrderID\(\)\n";
  print TCFILE "\t\tordId = Atr.getOrderID\(\)\n";
}

sub getSide{
foreach my $column (6 .. $eSheet_Gen->{MaxCol}) {
        if ( defined $eSheet_Gen->{Cells}[$_[0]][$column] && defined $eSheet_Gen->{Cells}[$_[0]+1][$column]) {
        if ($eSheet_Gen->{Cells}[$_[0]][$column]->Value ne '' &&  $eSheet_Gen->{Cells}[$_[0]+1][$column]->Value ne '') {
            $acn_tag = $eSheet_Gen->{Cells}[$_[0]][$column]->Value;
            $acn_data =  $eSheet_Gen->{Cells}[$_[0]+1][$column]->Value;
            if ( $acn_tag=~/Side/ ) {
                return $acn_data;
            }

}
}
}
return "None";
}
