<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="content-type" content="text/html;charset=utf-8" />
    <link href="theme/favicon.ico" rel="shortcut icon" type="image/x-icon" />
    <link href="theme/debgit.css" rel="stylesheet" type="text/css" />
    <title>Judd - a window into the Ultimate Debian Database</title>
    <style type="text/css">
    code {
        font-family: monospace;
        font-size: 100%;
        color: #333399;
    }
    .example {
        font-family: monospace;
        border: 1px solid #000099;
        background-color: #fcfcff;
        margin: 1em;
        padding: 0.3em;
        text-indent: -1.0em;
        padding-left: 2em;
    }
    .input {
        background-color: #eeeeff;
    }
    .input:before {
        content: "→ ";
    }
    .output:before {
        content: "← ";
    }
    .var {
        font-style: italic;
    }
    .input.synopsis {
        margin-bottom: 0.3em;
        background-color: #eeffee;
    }

    div.title {
        color: #527bbd;
        font-family: sans-serif;
        font-weight: bold;
        text-align: left;
        margin-top: 1.0em;
        margin-bottom: 0.5em;
    }
    .icon {
        vertical-align: top;
        font-size: 1.1em;
        font-weight: bold;
        text-decoration: underline;
        color: #527bbd;
        padding-right: 0.5em;
    }
    h2 {
        border-top: 1px solid #000099;
        padding-top: 0.5em;
        margin-top: 1em;
    }
    </style>
</head>
<body>

<?php

include "theme/debheader.html";

include "contents.html";
include "about.html";
include "judd-binarypackages.html";
include "judd-sourcepackages.html";
include "judd-bugs.html";
include "piccy-hardware.html";
include "piccy-kernel.html";

?>

<h2>Source code</h2>
<p>The latest source code for the <code>Judd</code> and <code>Piccy</code>
plugins can be found in
<a href="http://git.nanonanonano.net/?p=judd.git;a=summary">gitweb</a>.
</p>
<p>
<code>git clone http://git.nanonanonano.net/projects/judd.git</code>
</p>

<br />

<?

include "theme/debfooter.html";

?>

</body>
</html>

