pdf="$1"

if [ -z "$pdf" ]; then
	echo "Usage: $0 file.pdf"
	exit 1
fi

# 92.903 => 1024 x 576
# 116 => 1279 x 719
# 116.129 => 1280 x 720
# 150 => 827 x 465   => this was at 50% scale prolly
# 160 => 1764 x 992
rm -rf slides
mkdir slides
#convert -density 150 "$pdf" slides/slide%02d.png
#convert -density 232 "$pdf" slides/slide%02d.png
#convert -density 160 "$pdf" slides/slide%02d.png
#convert -density 116 "$pdf" slides/slide%02d.png
magick -density 116.129 "$pdf" slides/slide%02d.png
#convert -density 92.903 "$pdf" slides/slide%02d.png
