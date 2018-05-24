#!/usr/bin/perl

use strict;
use XML::Parser;
use LWP::Simple;
use CGI::Carp 'fatalsToBrowser';
use HTML::Entities;
use CGI;
use FCGI;

my $q = CGI->new;
my %attribs;
my %links;
my $curAttrib;
my @tags;

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

my $connCount = 0;

while (FCGI::accept >= 0) {
    my $tag = $q->param('tag');
    my $pagename = $tag ? join(' ',map(ucfirst,split(/,/,$tag))) : 'Random';

    print $q->header(-type=>"text/html; charset=utf-8");
    print '<!DOCTYPE html>
<html><head><title>The Flickr ' . $pagename . ' Image Generatr</title>
<style>
@import url("style.css");
';
    if (-f 'custom.css') {
	print '@import url("custom.css");';
    }

    print '</style>';

    if (-f "head.inc") {
	my $buf;
	open (ADBOX, "head.inc");
	while (read(ADBOX, $buf, 8192)) {
	    print $buf;
	}
	close (ADBOX);
    }
 
    print '</head>';

    print '<body>';


    print '<h1>The <a href="http://flickr.com/">Flickr</a> ' . $pagename . ' Image Generatr';
    if ($tag) {
	print '<span><a href="?">make it random</a></span>';
    }
    print '</h1>';

    print '<!--'.++$connCount.'-->';

    if (-f "header.inc") {
	my $buf;
	open (ADBOX, "header.inc");
	while (read(ADBOX, $buf, 8192)) {
	    print $buf;
	}
	close (ADBOX);
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

}
