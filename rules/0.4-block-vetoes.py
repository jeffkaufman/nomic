def should_block(pr):
    if pr.rejections:
        raise Exception('Rejected by: %s' % (' '.join(pr.rejections)))
