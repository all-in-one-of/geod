
def dump(geo, fh):

    N_vattr = geo.findVertexAttrib('N')
    N_pattr = geo.findPointAttrib('N')

    uv_vattr = geo.findVertexAttrib('uv')
    uv_pattr = geo.findPointAttrib('uv')

    for point in geo.points():
        fh.write('v %f %f %f\n' % tuple(point.position()))

    N_count = 0
    uv_count = 0

    faces = []

    for prim in geo.prims():

        face_parts = []

        for vert in prim.vertices():
            
            if N_vattr:
                N = vert.floatListAttribValue(N_vattr)
            elif N_pattr:
                N = vert.point().floatListAttribValue(N_pattr)
            else:
                N = None

            if N:
                N_count += 1
                fh.write('vn %f %f %f\n' % tuple(N))

            if uv_vattr:
                uv = vert.floatListAttribValue(uv_vattr)
            elif uv_pattr:
                uv = vert.point().floatListAttribValue(uv_pattr)
            else:
                uv = None

            if uv:
                uv_count += 1
                fh.write('vt %f %f %f\n' % tuple(uv))

            # We can't emit "%d//", or we will crash Maya. Silly.
            vert_parts = [
                str(vert.point().number() + 1),
                str(uv_count if uv else ''),
                str(N_count if N else ''),
            ]
            while not vert_parts[-1]:
                vert_parts.pop(-1)
            face_parts.append('/'.join(vert_parts))


        fh.write('f %s\n' % ' '.join(reversed(face_parts)))