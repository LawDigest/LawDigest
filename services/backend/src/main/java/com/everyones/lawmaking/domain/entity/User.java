package com.everyones.lawmaking.domain.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;
import lombok.*;
import lombok.experimental.SuperBuilder;

import java.util.List;


@Entity
@Data
@SuperBuilder
@Builder
@AllArgsConstructor(access = AccessLevel.PROTECTED)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class User extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name="user_id")
    private long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "auth_info_id")
    private AuthInfo authInfo;

    @OneToMany(mappedBy = "user")
    private List<CongressmanLike> congressManLike;

    @OneToMany(mappedBy = "user")
    private List<PartyFollow> partyFollow;

    @NotNull
    private String email;

    @NotNull
    private String name;

    @NotNull
    @Column(name="image_url")
    private String imageUrl;

    @Enumerated(EnumType.STRING)
    @NotNull
    private Role role;


}
