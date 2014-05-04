#!/usr/bin/perl

use strict;
use XML::Parser;
use LWP::Simple;
use CGI::Carp 'fatalsToBrowser';
use HTML::Entities;
use CGI qw(:standard);

my $q = CGI->new;
my %attribs;
my %links;
my $curAttrib;
my @tags;

my $showads = 1;

my $showtags = ($ENV{'HTTP_USER_AGENT'} !~ qw(\+[a-z]*://));

sub handle_start {
        my ($expat, $type, %data) = @_;

	$curAttrib = $type;
	if ($type eq 'link') {
		$curAttrib = $data{'rel'};
		$links{$curAttrib} = $data{'href'};
	}
	if ($type eq 'category' && $data{'term'}) {
		push (@tags, $data{'term'});
	}
	undef $attribs{$curAttrib};

	if ($type eq 'entry') {
		undef %links;
		undef %attribs;
		@tags = ();
	}
}

sub handle_char {
	my ($expat, $text) = @_;
	if ($curAttrib) {
		$attribs{$curAttrib} .= $text;
	}
}

my $num = 0;

sub textybox {
	my ($text) = @_;
	return '<input type="text" class="code"'
		. ' value="' . encode_entities($text) . '"'
		. ' size="' . length($text) . '"'
		. ' onClick="this.select()" readonly>';
}

sub handle_end {
	my ($expat, $type) = @_;

	$curAttrib = undef;
	if ($type eq 'entry') {
		my $img = $links{'enclosure'};
		my $link = $links{'alternate'};
		my $author = encode_entities($attribs{'name'});
		my $authorPage = $attribs{'uri'};
		my $title = encode_entities($attribs{'title'});
		my $pubdate = $attribs{'published'};
		my $update = $attribs{'updated'};
		my $takedate = $attribs{'dc:date.Taken'};
		my $id = $attribs{'id'};
		my $userpic = $attribs{'flickr:buddyicon'};

		my @fields = split /"/,$attribs{'content'};
		my $thumbnail = $fields[7];
		my $thumbW = $fields[9];
		my $thumbH = $fields[11];
		
		print '<div class="image">';
		print '<a href="' . $link 
			. '"><img class="thumb" src="' . $thumbnail 
			. '" alt="' . $title . ' by ' . $author . '" title="' . $title . '"></a>';
		print '<div class="meta">';
		print '<a href="' . $authorPage . '"><img class="userpic" src="' . $userpic . '" alt="' . $author . '" title="more by ' . $author . '"></a>';
		print '<ul>';
		print '<li><span>Picture:</span> <a href="' . $link . '">' 
			. $attribs{'title'} . '</a> by <a href="' . $authorPage . '">' . $author . '</a></li>';
		#print '<li><span>Full-size image URL:</span> ' . $img . '</li>';
		print '<li><span>Full-size image code:</span> ' 
			.textybox('<a href="' . $link . '"><img src="' 
				. $img . '"></a>') . '</li>';

		print '<li><span>Thumbnail code:</span> '
			.textybox('<a href="' . $link . '"><img src="' 
			. $thumbnail . '"></a>') . '</li>';
		print '<li><span>Link code:</span> '
			.textybox('<a href="' . $links{'alternate'} 
			. '">[link text goes here]</a>') . '</li>';
		print '<li><span>Forum code:</span> '
			. textybox('[url=' . $links{'alternate'} 
			. '][img]' . $img . '[/img][/url]')
			. '</li>';
		if ($showtags && scalar @tags > 0) {
			print '<li class="tags"><span>See more:</span> ';
			foreach my $tag (@tags) {
				print ' <a rel="nofollow" href="?tag=' . encode_entities($tag)
					. '">' . $tag . '</a>';
			}
			print '</li>';
		}
		print '</ul>';
		print '</div></div>';
	}
}

my $tag = $q->param('tag');
my $pagename = $tag ? join(' ',map(ucfirst,split(/,/,$tag))) : 'Random';

print $q->header(-type=>"text/html; charset=utf-8");
print '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html><head><title>The Flickr ' . $pagename . ' Image Generatr</title>
<style type="text/css">
ul { list-style-type: none; margin: 4px 0px 0px 1em; padding: 0px 0px 0px 52px; }
li { margin-left: 2em; text-indent: -2em; }
img { border: solid black 1px; margin: 4px; vertical-align: middle; }
/*img.a { float: left; }
img.b { float: right; }*/
img.userpic { position: relative; float: left; left: 0ex; top: 0ex; }
h1 { border-bottom: double black 3px; }
.image { border-bottom: dotted black 1px; margin-bottom: 1ex; padding-bottom: 1ex; }
h1 span { font-size: x-small; font-weight: normal; float: right; }
.meta {
	background: #cccccc;
	-moz-border-radius: 1ex;
	-webkit-border-radius: 1ex;
	border-radius: 1ex; 
	max-width: 100%;
	overflow-x: hidden;
	padding-right: 1ex;
}
.meta span { font-weight: bold; }
.meta li { white-space: nowrap; }
.meta li.tags { white-space: normal; }
#footer { font-size: small; clear: both; margin-top: 1ex;}
#pw_adbox_70223_3_0 { float: right; }
input.code {
	background: #ffc;
	border: solid black 1px;
	padding: 2px;
	font-family: Monospace;
}

</style>
</head><body>
';


print '<h1>The <a href="http://flickr.com/">Flickr</a> ' . $pagename . ' Image Generatr';
if ($tag) {
	print '<span><a href="?">make it random</a></span>';
}
print '</h1>';

if ($showads) {
print <<EOF;
<!-- Project Wonderful Ad Box Loader -->
<!-- Put this after the <body> tag at the top of your page -->
<script type="text/javascript">
   (function(){function pw_load(){
      if(arguments.callee.z)return;else arguments.callee.z=true;
      var d=document;var s=d.createElement('script');
      var x=d.getElementsByTagName('script')[0];
      s.type='text/javascript';s.async=true;
      s.src='//www.projectwonderful.com/pwa.js';
      x.parentNode.insertBefore(s,x);}
   if (window.attachEvent){
    window.attachEvent('DOMContentLoaded',pw_load);
    window.attachEvent('onload',pw_load);}
   else{
    window.addEventListener('DOMContentLoaded',pw_load,false);
    window.addEventListener('load',pw_load,false);}})();
</script>
<!-- End Project Wonderful Ad Box Loader -->

<!-- Project Wonderful Ad Box Code -->
<div id="pw_adbox_70223_3_0"></div>
<script type="text/javascript"></script>
<noscript><map name="admap70223" id="admap70223"><area href="http://www.projectwonderful.com/out_nojs.php?r=0&c=0&id=70223&type=3" shape="rect" coords="0,0,160,600" title="" alt="" target="_blank" /></map>
<table cellpadding="0" cellspacing="0" style="width:160px;border-style:none;background-color:#ffffff;"><tr><td><img src="http://www.projectwonderful.com/nojs.php?id=70223&type=3" style="width:160px;height:600px;border-style:none;" usemap="#admap70223" alt="" /></td></tr><tr><td style="background-color:#ffffff;" colspan="1"><center><a style="font-size:10px;color:#0000ff;text-decoration:none;line-height:1.2;font-weight:bold;font-family:Tahoma, verdana,arial,helvetica,sans-serif;text-transform: none;letter-spacing:normal;text-shadow:none;white-space:normal;word-spacing:normal;" href="http://www.projectwonderful.com/advertisehere.php?id=70223&type=3" target="_blank">Ads by Project Wonderful!  Your ad here, right now: $0</a></center></td></tr></table>
</noscript>
<!-- End Project Wonderful Ad Box Code -->
EOF
}

my $parser = new XML::Parser(Handlers => {Start => \&handle_start,
					  End => \&handle_end,
					  Char => \&handle_char}) or die "Couldn't create parser";

my $feedUrl = 'http://api.flickr.com/services/feeds/photos_public.gne';
if ($tag) {
	$feedUrl .= '?tags=' . encode_entities($tag);
}
my $content = LWP::Simple::get($feedUrl);

print '<div id="images">';

$parser->parse($content) or die "Couldn't parse: $@";
print <<EOF
</div>

<div id="footer">This page is not affiliated with Flickr. For entertainment purposes only. Not to be taken internally. Images all taken from the <a href="$feedUrl">Flickr public RSS feed</a>.</div>

</body></html>

EOF

