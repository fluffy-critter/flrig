#!/usr/bin/perl

use CGI qw/:standard/;
use Digest::MD5 qw(md5_base64);
use MIME::Base64;
use File::Path qw(mkpath);
use POSIX qw/strftime/;

my $returning = 0;
my $q = new CGI;
my $reader = $q->cookie('reader');
if (!$reader) {
	$reader = md5_base64('stats' 
		. ' ' . $q->remote_host()
		. ' ' . $q->user_agent());
} else {
	$returning = 1;
}

my $cookie = cookie(-name => 'reader',
		-value => $reader,
		-expires => '+1M');

my $tid = $q->path_info();
if (!$tid) {
	$tid = "root";
}
$tid =~ tr/\/\./__/;
my $statdir = '../stats/tracking/' . $tid;
mkpath($statdir);

open LOG, '>>', $statdir . '/' . strftime('%Y-%m-%d',localtime);
print LOG time() 
	. '|' . $returning
	. '|' . $reader
	. '|' . $q->remote_host() 
	. '|' . $q->referer() 
	. '|' . $q->user_agent()
	. '|' . $q->query_string()
	. "\n";

print header(-type => 'image/gif',
	-cookie => $cookie,
	-'cache-control' => 'no-cache');

print decode_base64('R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==');
