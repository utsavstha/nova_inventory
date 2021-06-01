class Record:
    def __init__(self, uid, hawb, flags, last_imported, first_imported, fs_devan, of_location, of_devan, of_piece_count, piece_count_difference, fs_location, fs_piece_count, fs_primary_location, client_name, release_date, consignee):
        self.uid = uid
        self.hawb = hawb
        self.duplicate_flag = True if flags[0].strip() == "1" else False
        self.overdue_flag = True if flags[1].strip() == "1" else False
        self.total_sum_flag = True if flags[2].strip() == "1" else False
        self.verified_flag = True if flags[3].strip() == "1" else False
        self.released_flag = True if flags[4].strip() == "1" else False
        self.all_clear_flag = True if flags[5].strip() == "1" else False
        self.last_imported = last_imported
        self.first_imported = first_imported
        self.fs_devan = fs_devan
        self.of_location = of_location
        self.of_devan = of_devan
        self.of_piece_count = of_piece_count
        self.piece_count_difference = piece_count_difference
        self.fs_location = fs_location
        self.fs_piece_count = fs_piece_count
        self.fs_primary_location = fs_primary_location
        self.client_name = client_name
        self.release_date = release_date
        self.consignee = consignee
