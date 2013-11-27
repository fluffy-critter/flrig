#!/usr/bin/perl

use strict;
use XML::Parser;
use LWP::Simple;
use CGI::Carp 'fatalsToBrowser';
use HTML::Entities;
use CGI;

my $q = CGI->new;
my %attribs;
my %links;
my $curAttrib;
my @tags;

my $showads = 0;

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
		if (scalar @tags > 0) {
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
#side-ad { float: right; }
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
print '
<!-- Project Wonderful ad code -->
<script type="text/javascript">
   var pw_d=document;
   pw_d.projectwonderful_adbox_id = "57857";
   pw_d.projectwonderful_adbox_type = "1";
</script>
<script type="text/javascript" src="http://www.projectwonderful.com/ad_display.js"></script>
<!-- End of Project Wonderful ad code -->
';
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

