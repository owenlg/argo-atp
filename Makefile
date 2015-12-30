PKGNAME=argo-atp
SPECFILE=${PKGNAME}.spec
FILES=Makefile ${SPECFILE} CHANGES LICENSE MANIFEST.in README setup.py atp.logrotate
PKGVERSION=1.0.0

dist:
	rm -rf dist
	mkdir -p dist/${PKGNAME}-${PKGVERSION}
	cp -pr ${FILES} apache atp_synchronizer bin cron doc etc mysql_schema mywlcg-atp mywlcg-atp-api dist/${PKGNAME}-${PKGVERSION}/
	cd dist; tar cfz ../${PKGNAME}-${PKGVERSION}.tar.gz ${PKGNAME}-${PKGVERSION}
	rm -rf dist

sources: dist

srpm: dist
	  rpmbuild -ts --define='dist .el6' ${PKGNAME}-${PKGVERSION}.tar.gz

rpm: dist
	  rpmbuild -ta ${PKGNAME}-${PKGVERSION}.tar.gz

clean:  
	rm -rf dist MANIFEST *.tar.gz *.egg-info
	rm -rf dist
